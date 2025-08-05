"use client"

import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"
import { cn } from "@/lib/utils"

interface Sheet {
  id: string
  name: string
  data: any
}

interface SpreadsheetTabsProps {
  sheets: Sheet[]
  activeSheetId: string
  onSheetChange: (sheetId: string) => void
  onAddSheet: () => void
}

export function SpreadsheetTabs({ sheets, activeSheetId, onSheetChange, onAddSheet }: SpreadsheetTabsProps) {
  return (
    <div className="flex items-center border-t bg-gray-50 p-2">
      <div className="flex items-center gap-1">
        {sheets.map((sheet) => (
          <button
            key={sheet.id}
            onClick={() => onSheetChange(sheet.id)}
            className={cn(
              "px-4 py-2 text-sm rounded-t-lg border-b-2 transition-colors",
              activeSheetId === sheet.id
                ? "bg-white border-blue-500 text-blue-600 font-medium"
                : "bg-gray-100 border-transparent text-gray-600 hover:bg-gray-200",
            )}
          >
            {sheet.name}
          </button>
        ))}
      </div>

      <Button variant="ghost" size="sm" onClick={onAddSheet} className="ml-2">
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  )
}
