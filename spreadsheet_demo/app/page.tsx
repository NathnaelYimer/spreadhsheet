"use client"

import { useState, useEffect } from "react"
import { SpreadsheetWorkspace } from "@/components/spreadsheet/spreadsheet-workspace"
import { AuthProvider } from "@/components/auth/auth-provider"
import { Toaster } from "@/components/ui/toaster"
import { ThemeProvider } from "@/components/theme-provider"

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

interface SheetData {
  [key: string]: CellData
}

interface Sheet {
  id: string
  name: string
  data: SheetData
}

export default function HomePage() {
  const [sheets, setSheets] = useState<Sheet[]>([
    {
      id: "sheet1",
      name: "Sales Data",
      data: {
        A1: { value: "Product", style: { bold: true, backgroundColor: "#f3f4f6" } },
        B1: { value: "Q1 Sales", style: { bold: true, backgroundColor: "#f3f4f6" } },
        C1: { value: "Q2 Sales", style: { bold: true, backgroundColor: "#f3f4f6" } },
        D1: { value: "Total", style: { bold: true, backgroundColor: "#f3f4f6" } },
        A2: { value: "Laptops" },
        B2: { value: "15000" },
        C2: { value: "18000" },
        D2: { value: "=B2+C2", formula: "=B2+C2" },
        A3: { value: "Phones" },
        B3: { value: "25000" },
        C3: { value: "22000" },
        D3: { value: "=B3+C3", formula: "=B3+C3" },
        A4: { value: "Tablets" },
        B4: { value: "8000" },
        C4: { value: "12000" },
        D4: { value: "=B4+C4", formula: "=B4+C4" },
        A5: { value: "Total", style: { bold: true } },
        B5: { value: "=SUM(B2:B4)", formula: "=SUM(B2:B4)" },
        C5: { value: "=SUM(C2:C4)", formula: "=SUM(C2:C4)" },
        D5: { value: "=SUM(D2:D4)", formula: "=SUM(D2:D4)" },
      },
    },
    {
      id: "sheet2",
      name: "Inventory",
      data: {
        A1: { value: "Item", style: { bold: true, backgroundColor: "#f3f4f6" } },
        B1: { value: "Stock", style: { bold: true, backgroundColor: "#f3f4f6" } },
        C1: { value: "Price", style: { bold: true, backgroundColor: "#f3f4f6" } },
        D1: { value: "Value", style: { bold: true, backgroundColor: "#f3f4f6" } },
        A2: { value: "Widget A" },
        B2: { value: "100" },
        C2: { value: "25.50" },
        D2: { value: "=B2*C2", formula: "=B2*C2" },
        A3: { value: "Widget B" },
        B3: { value: "75" },
        C3: { value: "45.00" },
        D3: { value: "=B3*C3", formula: "=B3*C3" },
      },
    },
  ])

  const [activeSheetId, setActiveSheetId] = useState("sheet1")
  const [selectedCell, setSelectedCell] = useState<string | null>("A1")
  const [formulaBarValue, setFormulaBarValue] = useState("")

  const activeSheet = sheets.find((sheet) => sheet.id === activeSheetId)

  useEffect(() => {
    if (selectedCell && activeSheet) {
      const cellData = activeSheet.data[selectedCell]
      setFormulaBarValue(cellData?.formula || cellData?.value || "")
    }
  }, [selectedCell, activeSheet])

  const updateCellData = (cellId: string, data: Partial<CellData>) => {
    setSheets((prev) =>
      prev.map((sheet) =>
        sheet.id === activeSheetId
          ? {
              ...sheet,
              data: {
                ...sheet.data,
                [cellId]: { ...sheet.data[cellId], ...data },
              },
            }
          : sheet,
      ),
    )
  }

  const addNewSheet = () => {
    const newSheetId = `sheet${sheets.length + 1}`
    const newSheet: Sheet = {
      id: newSheetId,
      name: `Sheet ${sheets.length + 1}`,
      data: {},
    }
    setSheets((prev) => [...prev, newSheet])
    setActiveSheetId(newSheetId)
  }

  const exportToCSV = () => {
    if (!activeSheet) return

    const rows: string[][] = []
    const cellIds = Object.keys(activeSheet.data)

    // Find max row and column
    let maxRow = 0,
      maxCol = 0
    cellIds.forEach((cellId) => {
      const col = cellId.charCodeAt(0) - 65
      const row = Number.parseInt(cellId.slice(1)) - 1
      maxRow = Math.max(maxRow, row)
      maxCol = Math.max(maxCol, col)
    })

    // Create CSV data
    for (let r = 0; r <= maxRow; r++) {
      const row: string[] = []
      for (let c = 0; c <= maxCol; c++) {
        const cellId = String.fromCharCode(65 + c) + (r + 1)
        const cellData = activeSheet.data[cellId]
        row.push(cellData?.value || "")
      }
      rows.push(row)
    }

    const csvContent = rows.map((row) => row.map((cell) => `"${cell}"`).join(",")).join("\n")
    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${activeSheet.name}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <AuthProvider>
        <div className="min-h-screen bg-background">
          <SpreadsheetWorkspace />
          <Toaster />
        </div>
      </AuthProvider>
    </ThemeProvider>
  )
}
