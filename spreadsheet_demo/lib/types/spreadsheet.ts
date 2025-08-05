export interface CellData {
  value: string
  formula?: string
  style?: {
    bold?: boolean
    italic?: boolean
    underline?: boolean
    backgroundColor?: string
    textColor?: string
    textAlign?: "left" | "center" | "right"
    fontSize?: number
    format?: "text" | "number" | "currency" | "percentage" | "date"
  }
}

export interface Sheet {
  id: string
  name: string
  data: { [cellId: string]: CellData }
  created_at: string
  updated_at: string
}

export interface Spreadsheet {
  id: string
  user_id: string
  sheets: Sheet[]
  active_sheet_id: string
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  email: string
  user_metadata?: {
    avatar_url?: string
    full_name?: string
  }
}
