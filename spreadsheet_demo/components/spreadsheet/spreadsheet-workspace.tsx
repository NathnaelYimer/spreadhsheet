"use client"

import { useState, useEffect, useCallback } from "react"
import { SpreadsheetGrid } from "./spreadsheet-grid"
import { SpreadsheetToolbar } from "./spreadsheet-toolbar"
import { SpreadsheetTabs } from "./spreadsheet-tabs"
import { FormulaBar } from "./formula-bar"
import { SpreadsheetHeader } from "./spreadsheet-header"
import { CollaborationPanel } from "./collaboration-panel"
import { Card } from "@/components/ui/card"
import { useSpreadsheetStore } from "@/lib/stores/spreadsheet-store"
import { useAuth } from "@/hooks/use-auth" // Ensure this hook is correctly implemented and exported
import { useToast } from "@/hooks/use-toast" // Ensure this hook is correctly implemented and exported
import { supabase } from "@/lib/supabase/client"
import type { RealtimeChannel } from "@supabase/supabase-js"

export function SpreadsheetWorkspace() {
  const { user } = useAuth()
  const { toast } = useToast()
  const {
    sheets,
    activeSheetId,
    selectedCell,
    setActiveSheet,
    setSelectedCell,
    updateCell,
    addSheet,
    loadSpreadsheet,
    saveSpreadsheet,
  } = useSpreadsheetStore()

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [collaborators, setCollaborators] = useState<any[]>([])
  const [realtimeChannel, setRealtimeChannel] = useState<RealtimeChannel | null>(null)

  const activeSheet = sheets.find((sheet) => sheet.id === activeSheetId)

  // Load spreadsheet data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        await loadSpreadsheet(user?.id ?? "guest")
      } catch (error) {
        toast({
          title: "Error loading spreadsheet",
          description: "Failed to load your spreadsheet data",
          variant: "destructive",
        })
      } finally {
        setIsLoading(false)
      }
    }

    loadData()
  }, [user, loadSpreadsheet, toast])

  // Setup real-time collaboration
  useEffect(() => {
    if (!user || !activeSheetId) return

    const channel = supabase
      .channel(`spreadsheet:${activeSheetId}`)
      .on("presence", { event: "sync" }, () => {
        const state = channel.presenceState()
        const users = Object.values(state).flat()
        setCollaborators(users.filter((u: any) => u.user_id !== user.id))
      })
      .on("presence", { event: "join" }, ({ key, newPresences }) => {
        console.log("User joined:", newPresences)
      })
      .on("presence", { event: "leave" }, ({ key, leftPresences }) => {
        console.log("User left:", leftPresences)
      })
      .on("broadcast", { event: "cell_update" }, ({ payload }) => {
        if (payload.user_id !== user.id) {
          updateCell(payload.sheet_id, payload.cell_id, payload.data, false)
        }
      })
      .subscribe(async (status) => {
        if (status === "SUBSCRIBED") {
          await channel.track({
            user_id: user.id,
            user_email: user.email,
            online_at: new Date().toISOString(),
          })
        }
      })

    setRealtimeChannel(channel)

    return () => {
      channel.unsubscribe()
    }
  }, [user, activeSheetId, updateCell])

  // Auto-save functionality
  useEffect(() => {
    if (!user || isLoading) return

    const autoSave = async () => {
      setIsSaving(true)
      try {
        await saveSpreadsheet(user.id)
      } catch (error) {
        console.error("Auto-save failed:", error)
      } finally {
        setIsSaving(false)
      }
    }

    const interval = setInterval(autoSave, 30000) // Auto-save every 30 seconds
    return () => clearInterval(interval)
  }, [user, sheets, saveSpreadsheet, isLoading])

  const handleCellUpdate = useCallback(
    (cellId: string, data: any) => {
      if (!activeSheetId || !user) return

      updateCell(activeSheetId, cellId, data)

      // Broadcast to collaborators
      if (realtimeChannel) {
        realtimeChannel.send({
          type: "broadcast",
          event: "cell_update",
          payload: {
            sheet_id: activeSheetId,
            cell_id: cellId,
            data,
            user_id: user.id,
          },
        })
      }
    },
    [activeSheetId, user, updateCell, realtimeChannel],
  )

  const handleManualSave = async () => {
    if (!user) return

    setIsSaving(true)
    try {
      await saveSpreadsheet(user.id)
      toast({
        title: "Spreadsheet saved",
        description: "Your changes have been saved successfully",
      })
    } catch (error) {
      toast({
        title: "Save failed",
        description: "Failed to save your changes",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your spreadsheet...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <SpreadsheetHeader onSave={handleManualSave} isSaving={isSaving} collaborators={collaborators} />

      <div className="flex h-[calc(100vh-64px)]">
        <div className="flex-1 flex flex-col">
          <Card className="flex-1 m-4 shadow-lg">
            <SpreadsheetToolbar
              selectedCell={selectedCell}
              onCellStyleChange={(style) => {
                if (selectedCell) {
                  handleCellUpdate(selectedCell, { style })
                }
              }}
            />

            <FormulaBar
              selectedCell={selectedCell}
              cellData={activeSheet?.data[selectedCell || ""] || null}
              onCellUpdate={handleCellUpdate}
            />

            <div className="flex-1 overflow-hidden">
              <SpreadsheetGrid
                data={activeSheet?.data || {}}
                selectedCell={selectedCell}
                onCellSelect={setSelectedCell}
                onCellChange={handleCellUpdate}
                collaborators={collaborators}
              />
            </div>

            <SpreadsheetTabs
              sheets={sheets}
              activeSheetId={activeSheetId}
              onSheetChange={setActiveSheet}
              onAddSheet={addSheet}
            />
          </Card>
        </div>

        <CollaborationPanel collaborators={collaborators} />
      </div>
    </div>
  )
}
