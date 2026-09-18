import { Client } from '../types';

/**
 * Client configuration
 * Add your clients here with their aliases (how they appear in different systems)
 *
 * Example:
 * - In Google Calendar: "Meeting with Acme Corp"
 * - In Notion: "Acme"
 * - In Fathom: "Acme Corporation Call"
 * - In SiteChecker: Project ID "12345"
 */
export const clients: Client[] = [
  // Example client - replace with your actual clients
  // {
  //   id: 'acme',
  //   name: 'Acme Corporation',
  //   aliases: ['Acme', 'Acme Corp', 'ACME'],
  //   notionDatabaseId: 'abc123...',
  //   sitecheckerProjectId: '12345'
  // },
];

/**
 * Match a string to a client based on name or aliases
 */
export function matchClient(text: string): Client | undefined {
  const lowerText = text.toLowerCase();

  return clients.find(client => {
    // Check main name
    if (lowerText.includes(client.name.toLowerCase())) {
      return true;
    }

    // Check aliases
    return client.aliases.some(alias =>
      lowerText.includes(alias.toLowerCase())
    );
  });
}

/**
 * Get all client names and aliases for searching
 */
export function getAllClientIdentifiers(): string[] {
  const identifiers: string[] = [];

  for (const client of clients) {
    identifiers.push(client.name);
    identifiers.push(...client.aliases);
  }

  return identifiers;
}
