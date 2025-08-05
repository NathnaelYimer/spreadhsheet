"use client"

import type React from "react"

import { useState, useRef, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { FormulaEngine } from "@/lib/formula-engine"
import type { CellData } from "@/lib/types/spreadsheet"

interface SpreadsheetGridProps {
  data: { [key: string]: CellData }
  selectedCell: string | null
  onCellSelect: (cellId: string) => void
  onCellChange: (cellId: string, data: Partial<CellData>) => void
  collaborators: any[]
}

export function SpreadsheetGrid({
  data,
  selectedCell,
  onCellSelect,
  onCellChange,
  collaborators,
}: SpreadsheetGridProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null)
  const [editValue, setEditValue] = useState("")
  const [selectedRange, setSelectedRange] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const gridRef = useRef<HTMLDivElement>(null)

  const rows = 50
  const cols = 26
  const formulaEngine = new FormulaEngine()

  useEffect(() => {
    if (editingCell && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingCell])

  const getCellId = useCallback((row: number, col: number) => {
    return String.fromCharCode(65 + col) + (row + 1)
  }, [])

  const parseCellId = useCallback((cellId: string) => {
    const col = cellId.charCodeAt(0) - 65
    const row = Number.parseInt(cellId.slice(1)) - 1
    return { row, col }
  }, [])

  const handleCellClick = useCallback(
    (cellId: string, event: React.MouseEvent) => {
      if (event.shiftKey && selectedCell) {
        // Range selection
        const start = parseCellId(selectedCell)
        const end = parseCellId(cellId)

        const minRow = Math.min(start.row, end.row)
        const maxRow = Math.max(start.row, end.row)
        const minCol = Math.min(start.col, end.col)
        const maxCol = Math.max(start.col, end.col)

        const range: string[] = []
        for (let r = minRow; r <= maxRow; r++) {
          for (let c = minCol; c <= maxCol; c++) {
            range.push(getCellId(r, c))
          }
        }
        setSelectedRange(range)
      } else {
        setSelectedRange([])
        onCellSelect(cellId)
      }
    },
    [selectedCell, onCellSelect, parseCellId, getCellId],
  )

  const handleCellDoubleClick = useCallback(
    (cellId: string) => {
      setEditingCell(cellId)
      const cellData = data[cellId]
      setEditValue(cellData?.formula || cellData?.value || "")
    },
    [data],
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, cellId: string) => {
      switch (e.key) {
        case "Enter":
          if (!editingCell) {
            handleCellDoubleClick(cellId)
          }
          break
        case "Delete":
        case "Backspace":
          if (!editingCell && selectedRange.length > 0) {
            selectedRange.forEach((id) => {
              onCellChange(id, { value: "", formula: undefined })
            })
          } else if (!editingCell) {
            onCellChange(cellId, { value: "", formula: undefined })
          }
          break
        case "ArrowUp":
        case "ArrowDown":
        case "ArrowLeft":
        case "ArrowRight":
          if (!editingCell) {
            e.preventDefault()
            const { row, col } = parseCellId(cellId)
            let newRow = row
            let newCol = col

            switch (e.key) {
              case "ArrowUp":
                newRow = Math.max(0, row - 1)
                break
              case "ArrowDown":
                newRow = Math.min(rows - 1, row + 1)
                break
              case "ArrowLeft":
                newCol = Math.max(0, col - 1)
                break
              case "ArrowRight":
                newCol = Math.min(cols - 1, col + 1)
                break
            }

            const newCellId = getCellId(newRow, newCol)
            onCellSelect(newCellId)
          }
          break
      }
    },
    [editingCell, selectedRange, onCellChange, parseCellId, getCellId, onCellSelect, handleCellDoubleClick, rows, cols],
  )

  const handleInputKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        if (editingCell) {
          const isFormula = editValue.startsWith("=")
          let processedValue = editValue

          if (isFormula) {
            try {
              processedValue = formulaEngine.evaluate(editValue, data).toString()
            } catch (error) {
              processedValue = "#ERROR"
            }
          }

          onCellChange(editingCell, {
            value: processedValue,
            formula: isFormula ? editValue : undefined,
          })
        }
        setEditingCell(null)
        setEditValue("")
      } else if (e.key === "Escape") {
        setEditingCell(null)
        setEditValue("")
      }
    },
    [editingCell, editValue, onCellChange, formulaEngine, data],
  )

  const renderCell = useCallback(
    (row: number, col: number) => {
      const cellId = getCellId(row, col)
      const cellData = data[cellId]
      const isSelected = selectedCell === cellId
      const isInRange = selectedRange.includes(cellId)
      const isEditing = editingCell === cellId

      // Check if any collaborator is editing this cell
      const collaboratorEditing = collaborators.find((c) => c.editing_cell === cellId)

      let displayValue = cellData?.value || ""
      if (cellData?.formula && !isEditing) {
        try {
          displayValue = formulaEngine.evaluate(cellData.formula, data).toString()
        } catch {
          displayValue = "#ERROR"
        }
      }

      return (
        <div
          key={cellId}
          className={cn(
            "relative border border-gray-300 h-8 min-w-[80px] flex items-center px-2 text-sm cursor-cell select-none",
            "hover:bg-gray-50 focus:outline-none",
            isSelected && "ring-2 ring-blue-500 bg-blue-50 z-10",
            isInRange && "bg-blue-100",
            collaboratorEditing && "ring-2 ring-green-500 bg-green-50",
            cellData?.style?.bold && "font-bold",
            cellData?.style?.italic && "italic",
          )}
          style={{
            backgroundColor:
              isSelected || isInRange || collaboratorEditing ? undefined : cellData?.style?.backgroundColor,
            color: cellData?.style?.textColor,
            textAlign: cellData?.style?.textAlign || "left",
          }}
          onClick={(e) => handleCellClick(cellId, e)}
          onDoubleClick={() => handleCellDoubleClick(cellId)}
          onKeyDown={(e) => handleKeyDown(e, cellId)}
          tabIndex={0}
          data-cell-id={cellId}
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
            <span className="truncate w-full" title={displayValue}>
              {displayValue}
            </span>
          )}

          {collaboratorEditing && (
            <div
              className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white"
              style={{ backgroundColor: collaboratorEditing.color || "#10b981" }}
              title={`${collaboratorEditing.user_email} is editing`}
            />
          )}
        </div>
      )
    },
    [
      getCellId,
      data,
      selectedCell,
      selectedRange,
      editingCell,
      collaborators,
      formulaEngine,
      handleCellClick,
      handleCellDoubleClick,
      handleKeyDown,
      handleInputKeyDown,
      editValue,
    ],
  )

  return (
    <div className="overflow-auto h-full" ref={gridRef}>
      <div className="inline-block min-w-full">
        {/* Column headers */}
        <div className="flex sticky top-0 z-20 bg-white">
          <div className="w-12 h-8 border border-gray-300 bg-gray-100 flex items-center justify-center text-xs font-medium sticky left-0 z-30">
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
            <div className="w-12 h-8 border border-gray-300 bg-gray-100 flex items-center justify-center text-xs font-medium sticky left-0 z-10">
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
