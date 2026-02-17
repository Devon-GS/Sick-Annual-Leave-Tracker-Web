"use client";

import { useState } from "react";
import useSWR from "swr";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { EmployeeTable, type Employee } from "@/components/employee-table";
import { EmployeeFormDialog } from "@/components/employee-form-dialog";
import { LeaveFormDialog } from "@/components/leave-form-dialog";
import { EditLeaveDialog } from "@/components/edit-leave-dialog";
import { ViewLeaveDialog } from "@/components/view-leave-dialog";
import {
  UserPlus,
  UserCog,
  UserMinus,
  CalendarPlus,
  CalendarCog,
  ThermometerSun,
  ClipboardList,
  XCircle,
  Stethoscope,
} from "lucide-react";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function HomePage() {
  const {
    data: employees,
    mutate,
    isLoading,
  } = useSWR<Employee[]>("/api/employees", fetcher);

  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(
    null
  );

  // Dialogs
  const [addEmployeeOpen, setAddEmployeeOpen] = useState(false);
  const [editEmployeeOpen, setEditEmployeeOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [addAnnualLeaveOpen, setAddAnnualLeaveOpen] = useState(false);
  const [editAnnualLeaveOpen, setEditAnnualLeaveOpen] = useState(false);
  const [addSickLeaveOpen, setAddSickLeaveOpen] = useState(false);
  const [editSickLeaveOpen, setEditSickLeaveOpen] = useState(false);
  const [viewLeaveOpen, setViewLeaveOpen] = useState(false);

  function handleRefresh() {
    mutate();
  }

  function handleClear() {
    setSelectedEmployee(null);
  }

  async function handleDeleteEmployee() {
    if (!selectedEmployee) return;

    try {
      await fetch(`/api/employees?id=${selectedEmployee.id}`, {
        method: "DELETE",
      });
      setSelectedEmployee(null);
      mutate();
    } catch {
      // Error handled silently
    }
    setDeleteConfirmOpen(false);
  }

  function requireSelected(action: () => void) {
    if (!selectedEmployee) {
      return;
    }
    action();
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-foreground text-balance">
              Employee Leave Manager
            </h1>
            <p className="text-sm text-muted-foreground">
              Annual and sick leave management
            </p>
          </div>
          {selectedEmployee && (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-muted-foreground">Selected:</span>
              <span className="font-semibold text-foreground">
                {selectedEmployee.firstName} {selectedEmployee.lastName}
              </span>
              <span className="font-mono text-muted-foreground">
                ({selectedEmployee.id})
              </span>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleClear}>
                <XCircle className="h-4 w-4" />
                <span className="sr-only">Clear selection</span>
              </Button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 flex flex-col gap-6">
        {/* Employee Table */}
        <Card className="border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-foreground">
              Employees
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <p className="text-muted-foreground">Loading employees...</p>
              </div>
            ) : (
              <EmployeeTable
                employees={employees || []}
                selectedEmployee={selectedEmployee}
                onSelect={setSelectedEmployee}
              />
            )}
          </CardContent>
        </Card>

        {/* Action Sections */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Setup Employees */}
          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-foreground">
                Setup Employees
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Button
                variant="outline"
                className="justify-start gap-2"
                onClick={() => setAddEmployeeOpen(true)}
              >
                <UserPlus className="h-4 w-4" />
                Add Employee
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2"
                disabled={!selectedEmployee}
                onClick={() =>
                  requireSelected(() => setEditEmployeeOpen(true))
                }
              >
                <UserCog className="h-4 w-4" />
                Update Employee
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2 text-destructive hover:text-destructive"
                disabled={!selectedEmployee}
                onClick={() =>
                  requireSelected(() => setDeleteConfirmOpen(true))
                }
              >
                <UserMinus className="h-4 w-4" />
                Delete Employee
              </Button>
            </CardContent>
          </Card>

          {/* Annual Leave & Sick Leave */}
          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-foreground">
                Annual Leave
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Button
                variant="outline"
                className="justify-start gap-2"
                disabled={!selectedEmployee}
                onClick={() =>
                  requireSelected(() => setAddAnnualLeaveOpen(true))
                }
              >
                <CalendarPlus className="h-4 w-4" />
                Add Annual Leave
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2"
                onClick={() => setEditAnnualLeaveOpen(true)}
              >
                <CalendarCog className="h-4 w-4" />
                Edit Annual Leave
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-foreground">
                Sick Leave
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              <Button
                variant="outline"
                className="justify-start gap-2"
                disabled={!selectedEmployee}
                onClick={() =>
                  requireSelected(() => setAddSickLeaveOpen(true))
                }
              >
                <ThermometerSun className="h-4 w-4" />
                Add Sick Leave
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2"
                onClick={() => setEditSickLeaveOpen(true)}
              >
                <Stethoscope className="h-4 w-4" />
                Edit Sick Leave
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Documents */}
        <Card className="border-border">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-foreground">
              Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => setViewLeaveOpen(true)}
            >
              <ClipboardList className="h-4 w-4" />
              View All Leave
            </Button>
          </CardContent>
        </Card>
      </main>

      {/* Dialogs */}
      <EmployeeFormDialog
        open={addEmployeeOpen}
        onOpenChange={setAddEmployeeOpen}
        employee={null}
        mode="add"
        onSave={handleRefresh}
      />

      <EmployeeFormDialog
        open={editEmployeeOpen}
        onOpenChange={setEditEmployeeOpen}
        employee={selectedEmployee}
        mode="edit"
        onSave={handleRefresh}
      />

      <AlertDialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <AlertDialogContent className="bg-card text-card-foreground">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-foreground">Delete Employee</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete{" "}
              <strong>
                {selectedEmployee?.firstName} {selectedEmployee?.lastName}
              </strong>
              ? This will also delete all their leave records. This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteEmployee}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {selectedEmployee && (
        <>
          <LeaveFormDialog
            open={addAnnualLeaveOpen}
            onOpenChange={setAddAnnualLeaveOpen}
            employeeId={selectedEmployee.id}
            employeeName={selectedEmployee.firstName}
            type="annual"
            onSave={handleRefresh}
          />

          <LeaveFormDialog
            open={addSickLeaveOpen}
            onOpenChange={setAddSickLeaveOpen}
            employeeId={selectedEmployee.id}
            employeeName={selectedEmployee.firstName}
            type="sick"
            onSave={handleRefresh}
          />
        </>
      )}

      <EditLeaveDialog
        open={editAnnualLeaveOpen}
        onOpenChange={setEditAnnualLeaveOpen}
        type="annual"
        onSave={handleRefresh}
      />

      <EditLeaveDialog
        open={editSickLeaveOpen}
        onOpenChange={setEditSickLeaveOpen}
        type="sick"
        onSave={handleRefresh}
      />

      <ViewLeaveDialog
        open={viewLeaveOpen}
        onOpenChange={setViewLeaveOpen}
      />
    </div>
  );
}
