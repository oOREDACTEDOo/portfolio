#!/usr/bin/env python3
"""
Decrypt and re-encrypt the portfolio's password-gated reports.

The reports in reports/ are self-contained HTML wrappers: a login card plus an
inline AES-GCM payload, with the key derived from the password by PBKDF2-SHA256
at 600,000 iterations. There was no plaintext source in the repo, so any edit
meant decrypting by hand. This script exists so that stops being true.

    ./crypt.py decrypt reports/            -> writes plaintext to reports-src/
    ./crypt.py encrypt reports-src/        -> writes gated HTML back to reports/

Password comes from $REPORT_PASSWORD, or --password. Never hardcode it here.

No third-party crypto libs are installed on this machine (no cryptography, no
pycryptodome, no node), so PBKDF2 uses hashlib and the AES layer shells out to
openssl. AES-GCM is AES-CTR plus an authentication tag: for decryption we strip
the trailing 16-byte tag and run CTR from the GCM starting counter, and for
encryption we recompute the tag with GHASH so the browser's subtle.decrypt()
still verifies. That keeps the existing wrapper format working untouched.
"""

import argparse
import base64
import hashlib
import os
import re
import subprocess
import sys

ITERATIONS = 600_000
TAG_LEN = 16

PAYLOAD_RE = re.compile(r'D\s*=\s*(\{.*?\})\s*;', re.S)


def _field(blob, key):
    m = re.search(r'"%s"\s*:\s*"([^"]*)"' % key, blob)
    if not m:
        raise ValueError("payload is missing %r" % key)
    return base64.b64decode(m.group(1))


def derive_key(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS, 32)


def _aes_ctr(key, counter, data):
    """Raw AES-256-CTR via openssl. Same call encrypts and decrypts."""
    p = subprocess.run(
        ['openssl', 'enc', '-aes-256-ctr', '-K', key.hex(), '-iv', counter.hex()],
        input=data, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout


def _aes_ecb_block(key, block):
    """Encrypt one 16-byte block with AES-256-ECB, no padding. Needed for GHASH."""
    p = subprocess.run(
        ['openssl', 'enc', '-aes-256-ecb', '-K', key.hex(), '-nopad'],
        input=block, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode(errors='replace'))
    return p.stdout[:16]


def _ghash(h_key, aad, ciphertext):
    """GF(2^128) hash used by GCM to build the auth tag."""
    def mul(x, y):
        z, v = 0, y
        for i in range(127, -1, -1):
            if (x >> i) & 1:
                z ^= v
            if v & 1:
                v = (v >> 1) ^ (0xE1 << 120)
            else:
                v >>= 1
        return z

    def pad(b):
        return b + b'\x00' * (-len(b) % 16)

    h = int.from_bytes(h_key, 'big')
    y = 0
    stream = pad(aad) + pad(ciphertext)
    for i in range(0, len(stream), 16):
        y = mul(y ^ int.from_bytes(stream[i:i + 16], 'big'), h)
    lengths = (len(aad) * 8).to_bytes(8, 'big') + (len(ciphertext) * 8).to_bytes(8, 'big')
    y = mul(y ^ int.from_bytes(lengths, 'big'), h)
    return y.to_bytes(16, 'big')


def gcm_decrypt(key, iv, payload):
    body, tag = payload[:-TAG_LEN], payload[-TAG_LEN:]
    counter = iv + b'\x00\x00\x00\x02'
    plain = _aes_ctr(key, counter, body)
    expected = _gcm_tag(key, iv, body)
    if expected != tag:
        raise ValueError("authentication tag mismatch - wrong password?")
    return plain


def gcm_encrypt(key, iv, plaintext):
    counter = iv + b'\x00\x00\x00\x02'
    body = _aes_ctr(key, counter, plaintext)
    return body + _gcm_tag(key, iv, body)


def _gcm_tag(key, iv, ciphertext):
    h_key = _aes_ecb_block(key, b'\x00' * 16)
    j0 = iv + b'\x00\x00\x00\x01'
    s = _ghash(h_key, b'', ciphertext)
    mask = _aes_ecb_block(key, j0)
    return bytes(a ^ b for a, b in zip(s, mask))


def read_payload(path):
    src = open(path, encoding='utf-8', errors='replace').read()
    m = PAYLOAD_RE.search(src)
    if not m:
        return None
    blob = m.group(1)
    return {k: _field(blob, k) for k in ('salt', 'iv', 'ct')}, src


def cmd_decrypt(args):
    os.makedirs(args.dest, exist_ok=True)
    done = failed = skipped = 0
    for name in sorted(os.listdir(args.src)):
        if not name.endswith('.html'):
            continue
        path = os.path.join(args.src, name)
        got = read_payload(path)
        if not got:
            print("SKIP  %s (not an encrypted wrapper)" % name)
            skipped += 1
            continue
        parts, _ = got
        try:
            key = derive_key(args.password, parts['salt'])
            plain = gcm_decrypt(key, parts['iv'], parts['ct'])
        except Exception as e:
            print("FAIL  %s: %s" % (name, e))
            failed += 1
            continue
        out = os.path.join(args.dest, name)
        with open(out, 'wb') as fh:
            fh.write(plain)
        print("OK    %s -> %s (%d bytes)" % (name, out, len(plain)))
        done += 1
    print("\ndecrypted %d, skipped %d, failed %d" % (done, skipped, failed))
    return 1 if failed else 0


def cmd_encrypt(args):
    """Re-gate plaintext, reusing each report's existing wrapper as the shell."""
    done = failed = 0
    for name in sorted(os.listdir(args.src)):
        if not name.endswith('.html'):
            continue
        plain = open(os.path.join(args.src, name), 'rb').read()
        target = os.path.join(args.dest, name)
        if not os.path.exists(target):
            print("FAIL  %s: no existing wrapper at %s" % (name, target))
            failed += 1
            continue
        got = read_payload(target)
        if not got:
            print("FAIL  %s: target is not an encrypted wrapper" % name)
            failed += 1
            continue
        parts, shell = got
        salt = os.urandom(16)
        iv = os.urandom(12)
        key = derive_key(args.password, salt)
        ct = gcm_encrypt(key, iv, plain)
        new = '{"salt":"%s","iv":"%s","ct":"%s"}' % (
            base64.b64encode(salt).decode(),
            base64.b64encode(iv).decode(),
            base64.b64encode(ct).decode())
        updated = PAYLOAD_RE.sub(lambda m: 'D = %s;' % new, shell, count=1)
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(updated)
        print("OK    %s -> %s (%d bytes payload)" % (name, target, len(ct)))
        done += 1
    print("\nencrypted %d, failed %d" % (done, failed))
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['decrypt', 'encrypt'])
    ap.add_argument('src')
    ap.add_argument('--dest')
    ap.add_argument('--password', default=os.environ.get('REPORT_PASSWORD'))
    args = ap.parse_args()

    if not args.password:
        sys.exit("no password: set REPORT_PASSWORD or pass --password")
    if not args.dest:
        args.dest = 'reports-src' if args.mode == 'decrypt' else 'reports'

    return cmd_decrypt(args) if args.mode == 'decrypt' else cmd_encrypt(args)


if __name__ == '__main__':
    sys.exit(main())
