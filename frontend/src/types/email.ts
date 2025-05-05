export interface Email {
  id: string;
  subject: string;
  sender: string;
  sender_name: string;
  sender_email: string;
  recipient: string;
  date: string;
  body: string;
  summary: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_score: number;
  categories: string[];
  importance_score: number;
  action_items: string[];
  topics: string[];
  has_attachments: boolean;
  attachments?: Attachment[];
  starred: boolean;
  unread: boolean;
  labels?: string[];
  thread_id?: string;
  reply_to?: string;
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

export interface EmailFilter {
  category: string;
  timeRange: 'day' | 'week' | 'month' | 'all';
  sort: 'date' | 'importance' | 'sentiment';
  sentiment: 'all' | 'positive' | 'neutral' | 'negative';
  query?: string;
  label?: string;
  hasAttachments?: boolean;
  unread?: boolean;
  starred?: boolean;
}

export interface EmailsResponse {
  emails: Email[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    pages: number;
  };
}

export interface EmailAnalytics {
  totalEmails: number;
  emailTrend: number;
  averageSentimentScore: number;
  sentimentTrend: number;
  dominantSentiment: 'positive' | 'neutral' | 'negative';
  responseRate: number;
  responseRateTrend: number;
  highPriorityCount: number;
  priorityTrend: number;
  topSenders: {
    name: string;
    count: number;
  }[];
  topCategories: {
    name: string;
    count: number;
  }[];
  categoriesDistribution: {
    name: string;
    value: number;
  }[];
  volumeByDay: {
    date: string;
    positive: number;
    neutral: number;
    negative: number;
    total: number;
  }[];
  responseTimeAverage: number;
  actionItemsCount: number;
  attachmentsCount: number;
}

export interface EmailDetail extends Email {
  threadEmails?: Email[];
  relatedEmails?: Email[];
  analysis: {
    entities: {
      text: string;
      label: string;
      start: number;
      end: number;
    }[];
    keywords: string[];
    readingTime: number;
    languageDetection: {
      language: string;
      confidence: number;
    };
  };
} 