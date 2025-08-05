export class FormulaEngine {
  private functions: { [key: string]: Function } = {
    SUM: this.sum,
    AVERAGE: this.average,
    COUNT: this.count,
    MAX: this.max,
    MIN: this.min,
    IF: this.if,
    VLOOKUP: this.vlookup,
    CONCATENATE: this.concatenate,
    UPPER: this.upper,
    LOWER: this.lower,
    LEN: this.len,
  }

  evaluate(formula: string, data: { [key: string]: any }): number | string {
    if (!formula.startsWith("=")) {
      return formula
    }

    let expression = formula.slice(1).toUpperCase()

    // Handle function calls
    for (const [funcName, func] of Object.entries(this.functions)) {
      const regex = new RegExp(`${funcName}\$$([^)]+)\$$`, "gi")
      expression = expression.replace(regex, (match, args) => {
        try {
          const result = func.call(this, args, data)
          return result.toString()
        } catch (error) {
          return "#ERROR"
        }
      })
    }

    // Handle cell ranges (e.g., A1:A5)
    const rangeRegex = /([A-Z]+\d+):([A-Z]+\d+)/g
    expression = expression.replace(rangeRegex, (match, start, end) => {
      const values = this.getCellRange(start, end, data)
      return values.join(",")
    })

    // Handle individual cell references
    const cellRegex = /[A-Z]+\d+/g
    expression = expression.replace(cellRegex, (cellId) => {
      const cellValue = data[cellId]?.value || "0"
      const numValue = Number.parseFloat(cellValue)
      return isNaN(numValue) ? "0" : numValue.toString()
    })

    try {
      // Evaluate the final expression
      const result = Function(`"use strict"; return (${expression})`)()
      return isNaN(result) ? "#ERROR" : result
    } catch (error) {
      return "#ERROR"
    }
  }

  private getCellRange(start: string, end: string, data: { [key: string]: any }): number[] {
    const startCol = start.match(/[A-Z]+/)?.[0] || "A"
    const startRow = Number.parseInt(start.match(/\d+/)?.[0] || "1")
    const endCol = end.match(/[A-Z]+/)?.[0] || "A"
    const endRow = Number.parseInt(end.match(/\d+/)?.[0] || "1")

    const startColNum = this.columnToNumber(startCol)
    const endColNum = this.columnToNumber(endCol)

    const values: number[] = []
    for (let row = startRow; row <= endRow; row++) {
      for (let col = startColNum; col <= endColNum; col++) {
        const cellId = this.numberToColumn(col) + row
        const cellValue = data[cellId]?.value || "0"
        const numValue = Number.parseFloat(cellValue)
        if (!isNaN(numValue)) {
          values.push(numValue)
        }
      }
    }
    return values
  }

  private columnToNumber(column: string): number {
    let result = 0
    for (let i = 0; i < column.length; i++) {
      result = result * 26 + (column.charCodeAt(i) - 64)
    }
    return result
  }

  private numberToColumn(num: number): string {
    let result = ""
    while (num > 0) {
      num--
      result = String.fromCharCode(65 + (num % 26)) + result
      num = Math.floor(num / 26)
    }
    return result
  }

  // Function implementations
  private sum(args: string, data: { [key: string]: any }): number {
    const values = this.parseArgs(args, data)
    return values.reduce((sum, val) => sum + val, 0)
  }

  private average(args: string, data: { [key: string]: any }): number {
    const values = this.parseArgs(args, data)
    return values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0
  }

  private count(args: string, data: { [key: string]: any }): number {
    const values = this.parseArgs(args, data)
    return values.length
  }

  private max(args: string, data: { [key: string]: any }): number {
    const values = this.parseArgs(args, data)
    return values.length > 0 ? Math.max(...values) : 0
  }

  private min(args: string, data: { [key: string]: any }): number {
    const values = this.parseArgs(args, data)
    return values.length > 0 ? Math.min(...values) : 0
  }

  private if(args: string, data: { [key: string]: any }): string | number {
    const parts = args.split(",").map((part) => part.trim())
    if (parts.length !== 3) return "#ERROR"

    const condition = this.evaluate("=" + parts[0], data)
    const trueValue = parts[1].replace(/"/g, "")
    const falseValue = parts[2].replace(/"/g, "")

    return condition ? trueValue : falseValue
  }

  private vlookup(args: string, data: { [key: string]: any }): string | number {
    // Simplified VLOOKUP implementation
    return "#N/A"
  }

  private concatenate(args: string, data: { [key: string]: any }): string {
    const parts = args.split(",").map((part) => part.trim().replace(/"/g, ""))
    return parts.join("")
  }

  private upper(args: string, data: { [key: string]: any }): string {
    const value = args.trim().replace(/"/g, "")
    return value.toUpperCase()
  }

  private lower(args: string, data: { [key: string]: any }): string {
    const value = args.trim().replace(/"/g, "")
    return value.toLowerCase()
  }

  private len(args: string, data: { [key: string]: any }): number {
    const value = args.trim().replace(/"/g, "")
    return value.length
  }

  private parseArgs(args: string, data: { [key: string]: any }): number[] {
    const values: number[] = []
    const parts = args.split(",")

    for (const part of parts) {
      const trimmed = part.trim()

      // Check if it's a range
      if (trimmed.includes(":")) {
        const [start, end] = trimmed.split(":")
        const rangeValues = this.getCellRange(start.trim(), end.trim(), data)
        values.push(...rangeValues)
      } else {
        // Single cell or number
        const numValue = Number.parseFloat(trimmed)
        if (!isNaN(numValue)) {
          values.push(numValue)
        } else {
          // It's a cell reference
          const cellValue = data[trimmed]?.value || "0"
          const cellNum = Number.parseFloat(cellValue)
          if (!isNaN(cellNum)) {
            values.push(cellNum)
          }
        }
      }
    }

    return values
  }
}
