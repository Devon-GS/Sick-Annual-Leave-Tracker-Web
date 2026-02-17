"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";
import { Pencil, Trash2 } from "lucide-react";

interface LeaveRecord {
  rowid: number;
  id: string;
  firstName: string;
  leaveTaken: number;
  leaveStart: string;
  leaveEnd: string;
  comment: string;
}

interface EditLeaveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: "annual" | "sick";
  onSave: () => void;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function EditLeaveDialog({
  open,
  onOpenChange,
  type,
  onSave,
}: EditLeaveDialogProps) {
  const endpoint =
    type === "annual" ? "/api/annual-leave" : "/api/sick-leave";

  const { data: records, mutate } = useSWR<LeaveRecord[]>(
    open ? endpoint : null,
    fetcher
  );

  const [selectedRecord, setSelectedRecord] = useState<LeaveRecord | null>(
    null
  );
  const [editMode, setEditMode] = useState(false);
  const [leaveTaken, setLeaveTaken] = useState("");
  const [leaveStart, setLeaveStart] = useState("");
  const [leaveEnd, setLeaveEnd] = useState("");
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteRowid, setDeleteRowid] = useState<number | null>(null);

  useEffect(() => {
    setSelectedRecord(null);
    setEditMode(false);
    setError("");
  }, [open]);

  function handleSelectRecord(record: LeaveRecord) {
    setSelectedRecord(record);
    setLeaveTaken(String(record.leaveTaken));
    setLeaveStart(record.leaveStart);
    setLeaveEnd(record.leaveEnd);
    setComment(record.comment);
    setEditMode(true);
    setError("");
  }

  function handleClearEdit() {
    setSelectedRecord(null);
    setEditMode(false);
    setLeaveTaken("");
    setLeaveStart("");
    setLeaveEnd("");
    setComment("");
    setError("");
  }

  async function handleUpdate() {
    if (!selectedRecord) return;
    setLoading(true);
    setError("");

    try {
      const res = await fetch(endpoint, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rowid: selectedRecord.rowid,
          leaveTaken,
          leaveStart,
          leaveEnd,
          comment,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to update leave");
      }

      await mutate();
      handleClearEdit();
      onSave();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (deleteRowid === null) return;
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${endpoint}?rowid=${deleteRowid}`, {
        method: "DELETE",
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to delete leave");
      }

      await mutate();
      handleClearEdit();
      onSave();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
      setDeleteConfirmOpen(false);
      setDeleteRowid(null);
    }
  }

  function confirmDelete(rowid: number) {
    setDeleteRowid(rowid);
    setDeleteConfirmOpen(true);
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto bg-card text-card-foreground">
          <DialogHeader>
            <DialogTitle className="text-foreground">
              Edit {type === "annual" ? "Annual" : "Sick"} Leave
            </DialogTitle>
            <DialogDescription>
              Select a record below to edit or delete it.
            </DialogDescription>
          </DialogHeader>

          <div className="rounded-lg border border-border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-primary hover:bg-primary">
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    ID
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    Name
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    Days
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    Start
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    End
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold">
                    Comment
                  </TableHead>
                  <TableHead className="text-primary-foreground font-semibold text-center">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!records || records.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-6 text-muted-foreground"
                    >
                      No {type === "annual" ? "annual" : "sick"} leave records
                      found.
                    </TableCell>
                  </TableRow>
                ) : (
                  records.map((rec, index) => (
                    <TableRow
                      key={rec.rowid}
                      className={cn(
                        "cursor-pointer transition-colors",
                        selectedRecord?.rowid === rec.rowid
                          ? "bg-primary/15 hover:bg-primary/20"
                          : index % 2 === 0
                          ? "bg-card hover:bg-accent"
                          : "bg-accent/40 hover:bg-accent"
                      )}
                      onClick={() => handleSelectRecord(rec)}
                    >
                      <TableCell className="text-center font-mono text-foreground">
                        {rec.id}
                      </TableCell>
                      <TableCell className="text-center text-foreground">
                        {rec.firstName}
                      </TableCell>
                      <TableCell className="text-center text-foreground">
                        {rec.leaveTaken}
                      </TableCell>
                      <TableCell className="text-center text-foreground">
                        {rec.leaveStart}
                      </TableCell>
                      <TableCell className="text-center text-foreground">
                        {rec.leaveEnd}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-foreground">
                        {rec.comment}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectRecord(rec);
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            <span className="sr-only">Edit leave record</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-destructive hover:text-destructive"
                            onClick={(e) => {
                              e.stopPropagation();
                              confirmDelete(rec.rowid);
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            <span className="sr-only">Delete leave record</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {editMode && selectedRecord && (
            <div className="border border-border rounded-lg p-4 mt-4 bg-secondary/30">
              <h3 className="font-semibold mb-3 text-foreground">
                Editing record for {selectedRecord.firstName} (
                {selectedRecord.id})
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="edit-days" className="text-foreground">Leave Days</Label>
                  <Input
                    id="edit-days"
                    type="number"
                    step="0.5"
                    value={leaveTaken}
                    onChange={(e) => setLeaveTaken(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="edit-start" className="text-foreground">Start Date</Label>
                  <Input
                    id="edit-start"
                    value={leaveStart}
                    onChange={(e) => setLeaveStart(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="edit-end" className="text-foreground">End Date</Label>
                  <Input
                    id="edit-end"
                    value={leaveEnd}
                    onChange={(e) => setLeaveEnd(e.target.value)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="edit-comment" className="text-foreground">Comment</Label>
                  <Textarea
                    id="edit-comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
              {error && (
                <p className="text-sm text-destructive mt-2">{error}</p>
              )}
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={handleClearEdit}>
                  Cancel
                </Button>
                <Button onClick={handleUpdate} disabled={loading}>
                  {loading ? "Updating..." : "Update Leave"}
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => confirmDelete(selectedRecord.rowid)}
                  disabled={loading}
                >
                  Delete
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent className="bg-card text-card-foreground">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-foreground">Delete Leave Record</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this leave record? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
