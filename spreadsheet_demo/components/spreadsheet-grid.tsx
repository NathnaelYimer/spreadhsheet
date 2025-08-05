"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface CellData {
  value: string
  formula?: string
  style?: {
    bold?: boolean
    italic?: boolean
    backgroundColor?: string
    textColor?: string
    textAlign?: "left" | "center" | "right"
  }
}

interface SpreadsheetGridProps {
  data: { [key: string]: CellData }
  selectedCell: string | null
  onCellSelect: (cellId: string) => void
  onCellChange: (cellId: string, data: Partial<CellData>) => void
}

export function SpreadsheetGrid({ data, selectedCell, onCellSelect, onCellChange }: SpreadsheetGridProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const rows = 20
  const cols = 10

  useEffect(() => {
    if (editingCell && inputRef.current) {
      inputRef.current.focus()
    }
  }, [editingCell])

  const getCellId = (row: number, col: number) => {
    return String.fromCharCode(65 + col) + (row + 1)
  }

  const evaluateFormula = (formula: string, allData: { [key: string]: CellData }): string => {
    try {
      if (!formula.startsWith("=")) return formula

      let expression = formula.slice(1)

      // Handle SUM function
      const sumMatch = expression.match(/SUM$$([A-Z]\d+):([A-Z]\d+)$$/)
      if (sumMatch) {
        const [, startCell, endCell] = sumMatch
        const startCol = startCell.charCodeAt(0) - 65
        const startRow = Number.parseInt(startCell.slice(1)) - 1
        const endCol = endCell.charCodeAt(0) - 65
        const endRow = Number.parseInt(endCell.slice(1)) - 1

        let sum = 0
        for (let r = startRow; r <= endRow; r++) {
          for (let c = startCol; c <= endCol; c++) {
            const cellId = getCellId(r, c)
            const cellValue = allData[cellId]?.value || "0"
            const numValue = Number.parseFloat(cellValue)
            if (!isNaN(numValue)) {
              sum += numValue
            }
          }
        }
        expression = expression.replace(sumMatch[0], sum.toString())
      }

      // Handle cell references (e.g., B2, C3)
      const cellRefs = expression.match(/[A-Z]\d+/g)
      if (cellRefs) {
        cellRefs.forEach((cellRef) => {
          const cellValue = allData[cellRef]?.value || "0"
          const numValue = Number.parseFloat(cellValue)
          expression = expression.replace(cellRef, isNaN(numValue) ? "0" : numValue.toString())
        })
      }

      // Evaluate the expression
      const result = Function(`"use strict"; return (${expression})`)()
      return isNaN(result) ? "#ERROR" : result.toString()
    } catch {
      return "#ERROR"
    }
  }

  const handleCellDoubleClick = (cellId: string) => {
    setEditingCell(cellId)
    const cellData = data[cellId]
    setEditValue(cellData?.formula || cellData?.value || "")
  }

  const handleCellKeyDown = (e: React.KeyboardEvent, cellId: string) => {
    if (e.key === "Enter") {
      handleCellDoubleClick(cellId)
    }
  }

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      if (editingCell) {
        const isFormula = editValue.startsWith("=")
        onCellChange(editingCell, {
          value: isFormula ? evaluateFormula(editValue, data) : editValue,
          formula: isFormula ? editValue : undefined,
        })
      }
      setEditingCell(null)
      setEditValue("")
    } else if (e.key === "Escape") {
      setEditingCell(null)
      setEditValue("")
    }
  }

  const renderCell = (row: number, col: number) => {
    const cellId = getCellId(row, col)
    const cellData = data[cellId]
    const isSelected = selectedCell === cellId
    const isEditing = editingCell === cellId

    let displayValue = cellData?.value || ""
    if (cellData?.formula) {
      displayValue = evaluateFormula(cellData.formula, data)
    }

    return (
      <div
        key={cellId}
        className={cn(
          "relative border border-gray-300 h-8 min-w-[80px] flex items-center px-2 text-sm cursor-cell",
          isSelected && "ring-2 ring-blue-500 bg-blue-50",
          cellData?.style?.backgroundColor && `bg-[${cellData.style.backgroundColor}]`,
          cellData?.style?.bold && "font-bold",
          cellData?.style?.italic && "italic",
        )}
        style={{
          backgroundColor: cellData?.style?.backgroundColor,
          color: cellData?.style?.textColor,
          textAlign: cellData?.style?.textAlign || "left",
        }}
        onClick={() => onCellSelect(cellId)}
        onDoubleClick={() => handleCellDoubleClick(cellId)}
        onKeyDown={(e) => handleCellKeyDown(e, cellId)}
        tabIndex={0}
      >
        {isEditing ? (
          <input
            ref={inputRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleInputKeyDown}
            onBlur={() => {
              setEditingCell(null)
              setEditValue("")
            }}
            className="w-full h-full border-none outline-none bg-transparent"
          />
        ) : (
          <span className="truncate w-full">{displayValue}</span>
        )}
      </div>
    )
  }

  return (
    <div className="overflow-auto max-h-[500px]">
      <div className="inline-block">
        {/* Column headers */}
        <div className="flex">
          <div className="w-12 h-8 border border-gray-300 bg-gray-100 flex items-center justify-center text-xs font-medium">
            {""}
          </div>
          {Array.from({ length: cols }, (_, col) => (
            <div
              key={col}
              className="min-w-[80px] h-8 border border-gray-300 bg-gray-100 flex items-center justify-center text-xs font-medium"
            >
              {String.fromCharCode(65 + col)}
            </div>
          ))}
        </div>

        {/* Rows */}
        {Array.from({ length: rows }, (_, row) => (
          <div key={row} className="flex">
            {/* Row header */}
            <div className="w-12 h-8 border border-gray-300 bg-gray-100 flex items-center justify-center text-xs font-medium">
              {row + 1}
            </div>
            {/* Cells */}
            {Array.from({ length: cols }, (_, col) => renderCell(row, col))}
          </div>
        ))}
      </div>
    </div>
  )
}
