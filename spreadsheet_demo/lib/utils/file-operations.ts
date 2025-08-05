import * as XLSX from "xlsx"
import { saveAs } from "file-saver"
import type { Sheet, CellData } from "@/lib/types/spreadsheet"

export async function exportToExcel(sheet: Sheet) {
  const wb = XLSX.utils.book_new()

  // Convert sheet data to worksheet format
  const wsData: any[][] = []
  const cellIds = Object.keys(sheet.data)

  // Find max row and column
  let maxRow = 0,
    maxCol = 0
  cellIds.forEach((cellId) => {
    const col = cellId.charCodeAt(0) - 65
    const row = Number.parseInt(cellId.slice(1)) - 1
    maxRow = Math.max(maxRow, row)
    maxCol = Math.max(maxCol, col)
  })

  // Initialize array
  for (let r = 0; r <= maxRow; r++) {
    wsData[r] = new Array(maxCol + 1).fill("")
  }

  // Fill data
  cellIds.forEach((cellId) => {
    const col = cellId.charCodeAt(0) - 65
    const row = Number.parseInt(cellId.slice(1)) - 1
    const cellData = sheet.data[cellId]
    wsData[row][col] = cellData.value || ""
  })

  const ws = XLSX.utils.aoa_to_sheet(wsData)
  XLSX.utils.book_append_sheet(wb, ws, sheet.name)

  const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" })
  const blob = new Blob([excelBuffer], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" })
  saveAs(blob, `${sheet.name}.xlsx`)
}

export async function exportToCSV(sheet: Sheet) {
  const rows: string[][] = []
  const cellIds = Object.keys(sheet.data)

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
      const cellData = sheet.data[cellId]
      row.push(cellData?.value || "")
    }
    rows.push(row)
  }

  const csvContent = rows.map((row) => row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(",")).join("\n")

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
  saveAs(blob, `${sheet.name}.csv`)
}

export async function importFromFile(file: File): Promise<{ [cellId: string]: CellData }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      try {
        const data = e.target?.result
        const workbook = XLSX.read(data, { type: "binary" })
        const sheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })

        const cellData: { [cellId: string]: CellData } = {}

        jsonData.forEach((row: any, rowIndex: number) => {
          row.forEach((cell: any, colIndex: number) => {
            if (cell !== undefined && cell !== "") {
              const cellId = String.fromCharCode(65 + colIndex) + (rowIndex + 1)
              cellData[cellId] = {
                value: cell.toString(),
              }
            }
          })
        })

        resolve(cellData)
      } catch (error) {
        reject(error)
      }
    }

    reader.onerror = () => reject(new Error("Failed to read file"))
    reader.readAsBinaryString(file)
  })
}
