import { Client } from '@notionhq/client';
import { NotionTask, TaskToCreate } from '../types';
import { matchClient, clients } from '../config/clients';

export class NotionIntegration {
  private client: Client;

  constructor() {
    this.client = new Client({
      auth: process.env.NOTION_API_KEY
    });
  }

  /**
   * Fetch tasks from a Notion database
   */
  async getTasks(databaseId: string): Promise<NotionTask[]> {
    const tasks: NotionTask[] = [];

    let hasMore = true;
    let startCursor: string | undefined;

    while (hasMore) {
      const response = await this.client.databases.query({
        database_id: databaseId,
        start_cursor: startCursor,
        filter: {
          property: 'Status',
          status: {
            does_not_equal: 'Completed'
          }
        },
        sorts: [
          {
            property: 'Due Date',
            direction: 'ascending'
          }
        ]
      });

      for (const page of response.results) {
        if ('properties' in page) {
          const task = this.parseNotionPage(page);
          if (task) {
            tasks.push(task);
          }
        }
      }

      hasMore = response.has_more;
      startCursor = response.next_cursor || undefined;
    }

    return tasks;
  }

  /**
   * Fetch tasks from all client databases
   */
  async getAllClientTasks(): Promise<NotionTask[]> {
    const allTasks: NotionTask[] = [];

    // First try the main QSP database
    const mainDbId = process.env.NOTION_QSP_DATABASE_ID;
    if (mainDbId) {
      const mainTasks = await this.getTasks(mainDbId);
      allTasks.push(...mainTasks);
    }

    // Then fetch from client-specific databases
    for (const client of clients) {
      if (client.notionDatabaseId) {
        try {
          const clientTasks = await this.getTasks(client.notionDatabaseId);
          for (const task of clientTasks) {
            task.client = client.name;
          }
          allTasks.push(...clientTasks);
        } catch (error) {
          console.error(`Error fetching tasks for ${client.name}:`, error);
        }
      }
    }

    return allTasks;
  }

  /**
   * Parse a Notion page into a NotionTask
   */
  private parseNotionPage(page: any): NotionTask | null {
    const props = page.properties;

    // Get title
    const titleProp = props.Name || props.Title || props.Task;
    let title = '';
    if (titleProp?.title) {
      title = titleProp.title.map((t: any) => t.plain_text).join('');
    }

    if (!title) return null;

    // Get status
    let status: NotionTask['status'] = 'Not Started';
    const statusProp = props.Status;
    if (statusProp?.status?.name) {
      const statusName = statusProp.status.name.toLowerCase();
      if (statusName.includes('progress') || statusName.includes('doing')) {
        status = 'In Progress';
      } else if (statusName.includes('complete') || statusName.includes('done')) {
        status = 'Completed';
      } else if (statusName.includes('block')) {
        status = 'Blocked';
      }
    }

    // Get due date
    let dueDate: Date | undefined;
    const dateProp = props['Due Date'] || props.Due || props.Deadline;
    if (dateProp?.date?.start) {
      dueDate = new Date(dateProp.date.start);
    }

    // Get priority
    let priority: NotionTask['priority'];
    const priorityProp = props.Priority;
    if (priorityProp?.select?.name) {
      const priorityName = priorityProp.select.name.toLowerCase();
      if (priorityName.includes('high') || priorityName.includes('urgent')) {
        priority = 'High';
      } else if (priorityName.includes('medium') || priorityName.includes('normal')) {
        priority = 'Medium';
      } else {
        priority = 'Low';
      }
    }

    // Get client
    let clientName = '';
    const clientProp = props.Client || props.Account;
    if (clientProp?.select?.name) {
      clientName = clientProp.select.name;
    } else if (clientProp?.relation) {
      const matched = matchClient(title);
      clientName = matched?.name || '';
    }

    // Get QSP quarter
    let qspQuarter: string | undefined;
    const quarterProp = props.Quarter || props['QSP Quarter'] || props.Q;
    if (quarterProp?.select?.name) {
      qspQuarter = quarterProp.select.name;
    }

    // Get notes
    let notes: string | undefined;
    const notesProp = props.Notes || props.Description;
    if (notesProp?.rich_text) {
      notes = notesProp.rich_text.map((t: any) => t.plain_text).join('');
    }

    return {
      id: page.id,
      title,
      status,
      dueDate,
      priority,
      client: clientName,
      qspQuarter,
      notes,
      url: page.url
    };
  }

  /**
   * Create a new task in Notion
   */
  async createTask(task: TaskToCreate): Promise<{ id: string; url: string }> {
    const databaseId = process.env.NOTION_QSP_DATABASE_ID;
    if (!databaseId) {
      throw new Error('NOTION_QSP_DATABASE_ID not configured');
    }

    const properties: any = {
      Name: {
        title: [
          {
            text: {
              content: task.title
            }
          }
        ]
      }
    };

    if (task.client) {
      properties.Client = {
        select: {
          name: task.client
        }
      };
    }

    if (task.dueDate) {
      properties['Due Date'] = {
        date: {
          start: task.dueDate.toISOString().split('T')[0]
        }
      };
    }

    if (task.priority) {
      properties.Priority = {
        select: {
          name: task.priority
        }
      };
    }

    if (task.notes || task.source) {
      const noteContent = [
        task.notes || '',
        task.source ? `\n\nSource: ${task.source}` : ''
      ].join('').trim();

      properties.Notes = {
        rich_text: [
          {
            text: {
              content: noteContent
            }
          }
        ]
      };
    }

    const response = await this.client.pages.create({
      parent: {
        database_id: databaseId
      },
      properties
    });

    return {
      id: response.id,
      url: (response as any).url
    };
  }

  /**
   * Create multiple tasks at once
   */
  async createTasks(tasks: TaskToCreate[]): Promise<Array<{ id: string; url: string; title: string }>> {
    const results: Array<{ id: string; url: string; title: string }> = [];

    for (const task of tasks) {
      try {
        const result = await this.createTask(task);
        results.push({ ...result, title: task.title });
      } catch (error) {
        console.error(`Failed to create task "${task.title}":`, error);
      }
    }

    return results;
  }

  /**
   * Search for tasks by client
   */
  async searchByClient(clientName: string, databaseId: string): Promise<NotionTask[]> {
    const response = await this.client.databases.query({
      database_id: databaseId,
      filter: {
        or: [
          {
            property: 'Client',
            select: {
              equals: clientName
            }
          },
          {
            property: 'Name',
            title: {
              contains: clientName
            }
          }
        ]
      }
    });

    const tasks: NotionTask[] = [];
    for (const page of response.results) {
      if ('properties' in page) {
        const task = this.parseNotionPage(page);
        if (task) {
          tasks.push(task);
        }
      }
    }

    return tasks;
  }
}
