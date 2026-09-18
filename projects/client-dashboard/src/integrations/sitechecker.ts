import { RankingData, KeywordRanking } from '../types';
import { clients } from '../config/clients';

/**
 * SiteChecker API Integration
 * Documentation: https://sitechecker.pro/api-documentation/
 */
export class SiteCheckerIntegration {
  private apiKey: string;
  private baseUrl = 'https://api.sitechecker.pro/v1';

  constructor() {
    this.apiKey = process.env.SITECHECKER_API_KEY || '';
  }

  /**
   * Get ranking data for a specific project
   */
  async getProjectRankings(projectId: string): Promise<KeywordRanking[]> {
    const response = await fetch(
      `${this.baseUrl}/projects/${projectId}/rankings`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`SiteChecker API error: ${response.status}`);
    }

    const data = await response.json();
    return this.parseRankings(data);
  }

  /**
   * Get all projects
   */
  async getProjects(): Promise<{ id: string; name: string; domain: string }[]> {
    const response = await fetch(
      `${this.baseUrl}/projects`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`SiteChecker API error: ${response.status}`);
    }

    const data = await response.json();
    return data.projects || [];
  }

  /**
   * Fetch ranking data for all configured clients
   */
  async getAllClientRankings(): Promise<RankingData[]> {
    const allRankings: RankingData[] = [];

    for (const client of clients) {
      if (client.sitecheckerProjectId) {
        try {
          const keywords = await this.getProjectRankings(client.sitecheckerProjectId);
          const rankingData = this.calculateRankingStats(client.name, client.sitecheckerProjectId, keywords);
          allRankings.push(rankingData);
        } catch (error) {
          console.error(`Error fetching rankings for ${client.name}:`, error);
        }
      }
    }

    return allRankings;
  }

  /**
   * Parse raw API response into KeywordRanking objects
   */
  private parseRankings(data: any): KeywordRanking[] {
    const rankings: KeywordRanking[] = [];

    // Adjust based on actual SiteChecker API response structure
    const keywords = data.keywords || data.data || [];

    for (const kw of keywords) {
      rankings.push({
        keyword: kw.keyword || kw.query || '',
        position: kw.position || kw.rank || 0,
        previousPosition: kw.previous_position || kw.prev_rank,
        change: (kw.previous_position || kw.prev_rank || kw.position) - (kw.position || kw.rank || 0),
        url: kw.url || kw.landing_page || '',
        searchVolume: kw.search_volume || kw.volume
      });
    }

    return rankings;
  }

  /**
   * Calculate aggregate stats for ranking data
   */
  private calculateRankingStats(
    clientName: string,
    projectId: string,
    keywords: KeywordRanking[]
  ): RankingData {
    let improved = 0;
    let declined = 0;
    let unchanged = 0;
    let totalPosition = 0;

    for (const kw of keywords) {
      totalPosition += kw.position;

      if (kw.change > 0) {
        improved++;
      } else if (kw.change < 0) {
        declined++;
      } else {
        unchanged++;
      }
    }

    return {
      client: clientName,
      projectId,
      keywords,
      lastUpdated: new Date(),
      averagePosition: keywords.length > 0 ? totalPosition / keywords.length : 0,
      positionChanges: {
        improved,
        declined,
        unchanged
      }
    };
  }

  /**
   * Get top improving keywords
   */
  getTopImprovers(rankings: KeywordRanking[], limit: number = 5): KeywordRanking[] {
    return [...rankings]
      .filter(k => k.change > 0)
      .sort((a, b) => b.change - a.change)
      .slice(0, limit);
  }

  /**
   * Get keywords that dropped the most
   */
  getTopDecliners(rankings: KeywordRanking[], limit: number = 5): KeywordRanking[] {
    return [...rankings]
      .filter(k => k.change < 0)
      .sort((a, b) => a.change - b.change)
      .slice(0, limit);
  }

  /**
   * Get keywords ranking in top 10
   */
  getTopTenKeywords(rankings: KeywordRanking[]): KeywordRanking[] {
    return rankings.filter(k => k.position <= 10);
  }
}
