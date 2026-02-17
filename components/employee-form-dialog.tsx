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
import type { Employee } from "@/components/employee-table";

interface EmployeeFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  employee: Employee | null;
  mode: "add" | "edit";
  onSave: () => void;
}

export function EmployeeFormDialog({
  open,
  onOpenChange,
  employee,
  mode,
  onSave,
}: EmployeeFormDialogProps) {
  const [id, setId] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (mode === "edit" && employee) {
      setId(employee.id);
      setFirstName(employee.firstName);
      setLastName(employee.lastName);
      setStartDate(employee.startDate);
    } else {
      setId("");
      setFirstName("");
      setLastName("");
      setStartDate("");
    }
    setError("");
  }, [mode, employee, open]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/employees", {
        method: mode === "add" ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, firstName, lastName, startDate }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to save employee");
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
            {mode === "add" ? "Add Employee" : "Update Employee"}
          </DialogTitle>
          <DialogDescription>
            {mode === "add"
              ? "Enter the new employee details below."
              : "Update the employee details below."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="emp-id" className="text-foreground">ID</Label>
            <Input
              id="emp-id"
              value={id}
              onChange={(e) => setId(e.target.value)}
              placeholder="e.g. EMP001"
              disabled={mode === "edit"}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="emp-first" className="text-foreground">First Name</Label>
            <Input
              id="emp-first"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="First name"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="emp-last" className="text-foreground">Last Name</Label>
            <Input
              id="emp-last"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Last name"
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="emp-start" className="text-foreground">Start Date (DD/MM/YYYY)</Label>
            <Input
              id="emp-start"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="DD/MM/YYYY"
              required
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
              {loading ? "Saving..." : mode === "add" ? "Add Employee" : "Update Employee"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
