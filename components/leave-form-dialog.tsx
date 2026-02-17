"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface LeaveFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  employeeId: string;
  employeeName: string;
  type: "annual" | "sick";
  onSave: () => void;
}

export function LeaveFormDialog({
  open,
  onOpenChange,
  employeeId,
  employeeName,
  type,
  onSave,
}: LeaveFormDialogProps) {
  const [leaveTaken, setLeaveTaken] = useState("");
  const [leaveStart, setLeaveStart] = useState("");
  const [leaveEnd, setLeaveEnd] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLeaveTaken("");
    setLeaveStart("");
    setLeaveEnd("");
    setComment("");
    setError("");
  }, [open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const endpoint =
      type === "annual" ? "/api/annual-leave" : "/api/sick-leave";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: employeeId,
          firstName: employeeName,
          leaveTaken,
          leaveStart,
          leaveEnd,
          comment,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to add leave");
      }

      onSave();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-card text-card-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            Add {type === "annual" ? "Annual" : "Sick"} Leave
          </DialogTitle>
          <DialogDescription>
            Recording leave for {employeeName} ({employeeId})
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="leave-days" className="text-foreground">Leave Taken (days)</Label>
            <Input
              id="leave-days"
              type="number"
              step="0.5"
              min="0.5"
              value={leaveTaken}
              onChange={(e) => setLeaveTaken(e.target.value)}
              placeholder="Number of days"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="leave-start" className="text-foreground">Leave Start Date (DD/MM/YYYY)</Label>
            <Input
              id="leave-start"
              value={leaveStart}
              onChange={(e) => setLeaveStart(e.target.value)}
              placeholder="DD/MM/YYYY"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="leave-end" className="text-foreground">Leave End Date (DD/MM/YYYY)</Label>
            <Input
              id="leave-end"
              value={leaveEnd}
              onChange={(e) => setLeaveEnd(e.target.value)}
              placeholder="DD/MM/YYYY"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="leave-comment" className="text-foreground">Comment</Label>
            <Textarea
              id="leave-comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Optional comment..."
              rows={3}
            />
          </div>
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save Leave"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
