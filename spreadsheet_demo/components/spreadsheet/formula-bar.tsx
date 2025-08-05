"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Check, X, ActivityIcon as Function } from "lucide-react"
import type { CellData } from "@/lib/types/spreadsheet"

interface FormulaBarProps {
  selectedCell: string | null
  cellData: CellData | null
  onCellUpdate: (cellId: string, data: Partial<CellData>) => void
}

export function FormulaBar({ selectedCell, cellData, onCellUpdate }: FormulaBarProps) {
  const [value, setValue] = useState("")
  const [isEditing, setIsEditing] = useState(false)

  useEffect(() => {
    if (cellData) {
      setValue(cellData.formula || cellData.value || "")
    } else {
      setValue("")
    }
    setIsEditing(false)
  }, [selectedCell, cellData])

  const handleSubmit = () => {
    if (!selectedCell) return

    const isFormula = value.startsWith("=")
    onCellUpdate(selectedCell, {
      value: isFormula ? value : value,
      formula: isFormula ? value : undefined,
    })
    setIsEditing(false)
  }

  const handleCancel = () => {
    setValue(cellData?.formula || cellData?.value || "")
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSubmit()
    } else if (e.key === "Escape") {
      handleCancel()
    }
  }

  return (
    <div className="border-b p-2 flex items-center gap-2 bg-white">
      <div className="flex items-center gap-2 min-w-[100px]">
        <Function className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-gray-700 min-w-[40px]">{selectedCell || "A1"}</span>
      </div>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={handleSubmit} disabled={!isEditing} className="h-8 w-8 p-0">
          <Check className="h-4 w-4 text-green-600" />
        </Button>
        <Button variant="ghost" size="sm" onClick={handleCancel} disabled={!isEditing} className="h-8 w-8 p-0">
          <X className="h-4 w-4 text-red-600" />
        </Button>
      </div>

      <Input
        value={value}
        onChange={(e) => {
          setValue(e.target.value)
          setIsEditing(true)
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsEditing(true)}
        placeholder="Enter value or formula (e.g., =SUM(A1:A5))"
        className="flex-1 h-8"
      />
    </div>
  )
}
