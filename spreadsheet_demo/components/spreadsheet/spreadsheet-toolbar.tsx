"use client"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import {
  Bold,
  Italic,
  Underline,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Palette,
  Type,
  Percent,
  DollarSign,
  Hash,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

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
    { name: "Purple", value: "#f3e8ff" },
    { name: "Orange", value: "#fed7aa" },
  ]

  const textColors = [
    { name: "Black", value: "#000000" },
    { name: "Gray", value: "#6b7280" },
    { name: "Blue", value: "#2563eb" },
    { name: "Green", value: "#16a34a" },
    { name: "Red", value: "#dc2626" },
    { name: "Purple", value: "#9333ea" },
    { name: "Orange", value: "#ea580c" },
  ]

  const fontSizes = ["10", "11", "12", "14", "16", "18", "20", "24", "28", "32"]

  return (
    <div className="border-b p-3 flex items-center gap-3 bg-gray-50/50">
      {/* Font Controls */}
      <div className="flex items-center gap-2">
        <Select defaultValue="12">
          <SelectTrigger className="w-16 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {fontSizes.map((size) => (
              <SelectItem key={size} value={size}>
                {size}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Text Formatting */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ bold: true })} className="h-8 w-8 p-0">
          <Bold className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => onCellStyleChange({ italic: true })} className="h-8 w-8 p-0">
          <Italic className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ underline: true })}
          className="h-8 w-8 p-0"
        >
          <Underline className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Text Alignment */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ textAlign: "left" })}
          className="h-8 w-8 p-0"
        >
          <AlignLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ textAlign: "center" })}
          className="h-8 w-8 p-0"
        >
          <AlignCenter className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ textAlign: "right" })}
          className="h-8 w-8 p-0"
        >
          <AlignRight className="h-4 w-4" />
        </Button>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Colors */}
      <div className="flex items-center gap-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 px-2">
              <Palette className="h-4 w-4 mr-1" />
              Fill
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

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 px-2">
              <Type className="h-4 w-4 mr-1" />
              Text
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {textColors.map((color) => (
              <DropdownMenuItem
                key={color.value}
                onClick={() => onCellStyleChange({ textColor: color.value })}
                className="flex items-center gap-2"
              >
                <div className="w-4 h-4 rounded border" style={{ backgroundColor: color.value }} />
                {color.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Separator orientation="vertical" className="h-6" />

      {/* Number Formatting */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ format: "currency" })}
          className="h-8 w-8 p-0"
          title="Currency"
        >
          <DollarSign className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ format: "percentage" })}
          className="h-8 w-8 p-0"
          title="Percentage"
        >
          <Percent className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onCellStyleChange({ format: "number" })}
          className="h-8 w-8 p-0"
          title="Number"
        >
          <Hash className="h-4 w-4" />
        </Button>
      </div>

      <div className="ml-auto text-sm text-muted-foreground">{selectedCell && `Selected: ${selectedCell}`}</div>
    </div>
  )
}
