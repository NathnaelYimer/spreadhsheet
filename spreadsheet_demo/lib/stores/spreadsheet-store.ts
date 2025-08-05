"use client"

import { create } from "zustand"
import type { Sheet, CellData } from "@/lib/types/spreadsheet"
import { supabase } from "@/lib/supabase/client"

interface SpreadsheetStore {
  sheets: Sheet[]
  activeSheetId: string
  selectedCell: string | null
  setSheets: (sheets: Sheet[]) => void
  setActiveSheet: (sheetId: string) => void
  setSelectedCell: (cellId: string | null) => void
  updateCell: (sheetId: string, cellId: string, data: Partial<CellData>, broadcast?: boolean) => void
  addSheet: () => void
  deleteSheet: (sheetId: string) => void
  loadSpreadsheet: (userId: string) => Promise<void>
  saveSpreadsheet: (userId: string) => Promise<void>
}

export const useSpreadsheetStore = create<SpreadsheetStore>((set, get) => ({
  sheets: [
    {
      id: "sheet1",
      name: "Sheet 1",
      data: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
  activeSheetId: "sheet1",
  selectedCell: null,

  setSheets: (sheets) => set({ sheets }),

  setActiveSheet: (sheetId) => set({ activeSheetId: sheetId }),

  setSelectedCell: (cellId) => set({ selectedCell: cellId }),

  updateCell: (sheetId, cellId, data, broadcast = true) => {
    set((state) => ({
      sheets: state.sheets.map((sheet) =>
        sheet.id === sheetId
          ? {
              ...sheet,
              data: {
                ...sheet.data,
                [cellId]: { ...sheet.data[cellId], ...data },
              },
              updated_at: new Date().toISOString(),
            }
          : sheet,
      ),
    }))
  },

  addSheet: () => {
    const { sheets } = get()
    const newSheetId = `sheet${Date.now()}`
    const newSheet: Sheet = {
      id: newSheetId,
      name: `Sheet ${sheets.length + 1}`,
      data: {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    set((state) => ({
      sheets: [...state.sheets, newSheet],
      activeSheetId: newSheetId,
    }))
  },

  deleteSheet: (sheetId) => {
    const { sheets, activeSheetId } = get()
    if (sheets.length <= 1) return // Don't delete the last sheet

    const newSheets = sheets.filter((sheet) => sheet.id !== sheetId)
    const newActiveSheetId = activeSheetId === sheetId ? newSheets[0].id : activeSheetId

    set({
      sheets: newSheets,
      activeSheetId: newActiveSheetId,
    })
  },

  loadSpreadsheet: async (userId) => {
    // If userId is 'guest', just use a default local sheet and don't call Supabase
    if (userId === 'guest') {
      set({
        sheets: [
          {
            id: "sheet1",
            name: "Sheet 1",
            data: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
        activeSheetId: "sheet1",
      })
      return
    }
    try {
      const { data, error } = await supabase.from("spreadsheets").select("*").eq("user_id", userId).single()

      if (error && error.code !== "PGRST116") {
        throw error
      }

      if (data) {
        set({
          sheets: data.sheets || [
            {
              id: "sheet1",
              name: "Sheet 1",
              data: {},
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          activeSheetId: data.active_sheet_id || "sheet1",
        })
      }
    } catch (error) {
      console.error("Error loading spreadsheet:", error)
      throw error
    }
  },

  saveSpreadsheet: async (userId) => {
    const { sheets, activeSheetId } = get()

    try {
      const { error } = await supabase.from("spreadsheets").upsert({
        user_id: userId,
        sheets,
        active_sheet_id: activeSheetId,
        updated_at: new Date().toISOString(),
      })

      if (error) throw error
    } catch (error) {
      console.error("Error saving spreadsheet:", error)
      throw error
    }
  },
}))
