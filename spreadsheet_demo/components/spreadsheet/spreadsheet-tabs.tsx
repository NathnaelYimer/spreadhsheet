"use client"

import { Button } from "@/components/ui/button"
import { Plus, X } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Sheet } from "@/lib/types/spreadsheet"

interface SpreadsheetTabsProps {
  sheets: Sheet[]
  activeSheetId: string
  onSheetChange: (sheetId: string) => void
  onAddSheet: () => void
}

export function SpreadsheetTabs({ sheets, activeSheetId, onSheetChange, onAddSheet }: SpreadsheetTabsProps) {
  return (
    <div className="flex items-center border-t bg-gray-50 p-2 min-h-[48px]">
      <div className="flex items-center gap-1 flex-1 overflow-x-auto">
        {sheets.map((sheet) => (
          <div
            key={sheet.id}
            className={cn(
              "group flex items-center gap-2 px-4 py-2 text-sm rounded-t-lg border-b-2 transition-all cursor-pointer min-w-[120px]",
              activeSheetId === sheet.id
                ? "bg-white border-blue-500 text-blue-600 font-medium shadow-sm"
                : "bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200",
            )}
            onClick={() => onSheetChange(sheet.id)}
          >
            <span className="truncate flex-1">{sheet.name}</span>
            {sheets.length > 1 && (
              <Button
                variant="ghost"
                size="sm"
                className="h-4 w-4 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => {
                  e.stopPropagation()
                  // Handle sheet deletion
                }}
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        ))}
      </div>

      <Button variant="ghost" size="sm" onClick={onAddSheet} className="ml-2 h-8 w-8 p-0" title="Add new sheet">
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  )
}
