"use client"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Bold, Italic, AlignLeft, AlignCenter, AlignRight, Palette } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

interface SpreadsheetToolbarProps {
  selectedCell: string | null
  onCellStyleChange: (style: any) => void
}

export function SpreadsheetToolbar({ selectedCell, onCellStyleChange }: SpreadsheetToolbarProps) {
  const colors = [
    { name: "White", value: "#ffffff" },
    { name: "Light Gray", value: "#f3f4f6" },
    { name: "Blue", value: "#dbeafe" },
    { name: "Green", value: "#dcfce7" },
    { name: "Yellow", value: "#fef3c7" },
    { name: "Red", value: "#fee2e2" },
  ]

  return (
    <div className="border-b p-2 flex items-center gap-2">
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ bold: true })}>
          <Bold className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ italic: true })}>
          <Italic className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ textAlign: "left" })}>
          <AlignLeft className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ textAlign: "center" })}>
          <AlignCenter className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ textAlign: "right" })}>
          <AlignRight className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <Palette className="h-4 w-4 mr-2" />
            Background
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          {colors.map((color) => (
            <DropdownMenuItem
              key={color.value}
              onClick={() => onCellStyleChange({ backgroundColor: color.value })}
              className="flex items-center gap-2"
            >
              <div className="w-4 h-4 rounded border" style={{ backgroundColor: color.value }} />
              {color.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="ml-auto text-sm text-gray-600">{selectedCell && `Selected: ${selectedCell}`}</div>
    </div>
  )
}
