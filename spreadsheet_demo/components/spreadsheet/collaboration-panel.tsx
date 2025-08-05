"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Users, Circle } from "lucide-react"

interface CollaborationPanelProps {
  collaborators: any[]
}

export function CollaborationPanel({ collaborators }: CollaborationPanelProps) {
  if (collaborators.length === 0) {
    return null
  }

  return (
    <Card className="w-80 m-4 ml-0">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Users className="h-4 w-4" />
          Active Collaborators ({collaborators.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {collaborators.map((collaborator, index) => (
          <div key={index} className="flex items-center gap-3">
            <Avatar className="h-8 w-8">
              <AvatarImage src={collaborator.avatar_url || "/placeholder.svg"} />
              <AvatarFallback className="text-xs">{collaborator.user_email?.charAt(0).toUpperCase()}</AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{collaborator.user_email}</p>
              <div className="flex items-center gap-2 mt-1">
                <Circle className="h-2 w-2 fill-green-500 text-green-500" />
                <span className="text-xs text-muted-foreground">Online</span>
                {collaborator.editing_cell && (
                  <Badge variant="secondary" className="text-xs">
                    Editing {collaborator.editing_cell}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
