"use client"

import type React from "react"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Download, Upload, Save, FileSpreadsheet, Share2, Settings, Users } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { useSpreadsheetStore } from "@/lib/stores/spreadsheet-store"
import { exportToExcel, exportToCSV, importFromFile } from "@/lib/utils/file-operations"
import { useToast } from "@/hooks/use-toast"

interface SpreadsheetHeaderProps {
  onSave: () => void
  isSaving: boolean
  collaborators: any[]
}

export function SpreadsheetHeader({ onSave, isSaving, collaborators }: SpreadsheetHeaderProps) {
  const { user, signOut } = useAuth()
  const { sheets, activeSheetId } = useSpreadsheetStore()
  const { toast } = useToast()

  const activeSheet = sheets.find((sheet) => sheet.id === activeSheetId)

  const handleExportExcel = async () => {
    if (!activeSheet) return

    try {
      await exportToExcel(activeSheet)
      toast({
        title: "Export successful",
        description: "Spreadsheet exported to Excel format",
      })
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export spreadsheet",
        variant: "destructive",
      })
    }
  }

  const handleExportCSV = async () => {
    if (!activeSheet) return

    try {
      await exportToCSV(activeSheet)
      toast({
        title: "Export successful",
        description: "Spreadsheet exported to CSV format",
      })
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export spreadsheet",
        variant: "destructive",
      })
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const data = await importFromFile(file)
      // Handle imported data
      toast({
        title: "Import successful",
        description: "File imported successfully",
      })
    } catch (error) {
      toast({
        title: "Import failed",
        description: "Failed to import file",
        variant: "destructive",
      })
    }
  }

  return (
    <header className="border-b bg-white px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="h-6 w-6 text-blue-600" />
          <h1 className="text-lg font-semibold text-gray-900">{activeSheet?.name || "Spreadsheet"}</h1>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onSave} disabled={isSaving}>
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? "Saving..." : "Save"}
          </Button>

          <Button variant="outline" size="sm" onClick={handleExportExcel}>
            <Download className="h-4 w-4 mr-2" />
            Excel
          </Button>

          <Button variant="outline" size="sm" onClick={handleExportCSV}>
            <Download className="h-4 w-4 mr-2" />
            CSV
          </Button>

          <div className="relative">
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleImport}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Button variant="outline" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
          </div>

          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Collaborators */}
        {collaborators.length > 0 && (
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <div className="flex -space-x-2">
              {collaborators.slice(0, 3).map((collaborator, index) => (
                <Avatar key={index} className="h-8 w-8 border-2 border-white">
                  <AvatarImage src={collaborator.avatar_url || "/placeholder.svg"} />
                  <AvatarFallback className="text-xs">
                    {collaborator.user_email?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              ))}
              {collaborators.length > 3 && (
                <div className="h-8 w-8 rounded-full bg-gray-100 border-2 border-white flex items-center justify-center text-xs font-medium">
                  +{collaborators.length - 3}
                </div>
              )}
            </div>
          </div>
        )}

        <Separator orientation="vertical" className="h-6" />

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>

          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.user_metadata?.avatar_url || "/placeholder.svg"} />
            <AvatarFallback>{user?.email?.charAt(0).toUpperCase()}</AvatarFallback>
          </Avatar>

          <Button variant="ghost" size="sm" onClick={signOut}>
            Sign Out
          </Button>
        </div>
      </div>
    </header>
  )
}
