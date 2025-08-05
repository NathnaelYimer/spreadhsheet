"use client"

import type React from "react"

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Check, X } from "lucide-react"

interface FormulaBarProps {
  value: string
  selectedCell: string | null
  onChange: (value: string) => void
  onSubmit: (value: string) => void
}

export function FormulaBar({ value, selectedCell, onChange, onSubmit }: FormulaBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onSubmit(value)
    }
  }

  return (
    <div className="border-b p-2 flex items-center gap-2 bg-gray-50">
      <div className="flex items-center gap-2 min-w-[100px]">
        <span className="text-sm font-medium text-gray-700">{selectedCell || "A1"}</span>
      </div>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onSubmit(value)}>
          <Check className="h-4 w-4 text-green-600" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onChange("")}>
          <X className="h-4 w-4 text-red-600" />
        </Button>
      </div>

      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter value or formula (e.g., =SUM(A1:A5))"
        className="flex-1"
      />
    </div>
  )
}
