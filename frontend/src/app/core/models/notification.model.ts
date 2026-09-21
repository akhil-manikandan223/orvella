export interface NotificationRead {
  id: string;
  type: string;
  title: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export interface UnreadCountRead {
  unread_count: number;
}
