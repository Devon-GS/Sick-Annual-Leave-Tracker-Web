"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export interface Employee {
  id: string;
  firstName: string;
  lastName: string;
  startDate: string;
  leaveAvailable: number;
  sickLeaveAvailable: number;
}

interface EmployeeTableProps {
  employees: Employee[];
  selectedEmployee: Employee | null;
  onSelect: (employee: Employee) => void;
}

export function EmployeeTable({
  employees,
  selectedEmployee,
  onSelect,
}: EmployeeTableProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-primary hover:bg-primary">
            <TableHead className="text-primary-foreground font-semibold text-center">
              ID
            </TableHead>
            <TableHead className="text-primary-foreground font-semibold text-center">
              First Name
            </TableHead>
            <TableHead className="text-primary-foreground font-semibold text-center">
              Last Name
            </TableHead>
            <TableHead className="text-primary-foreground font-semibold text-center">
              Start Date
            </TableHead>
            <TableHead className="text-primary-foreground font-semibold text-center">
              Leave Available
            </TableHead>
            <TableHead className="text-primary-foreground font-semibold text-center">
              Sick Leave Available
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {employees.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-center py-8 text-muted-foreground"
              >
                No employees found. Add an employee to get started.
              </TableCell>
            </TableRow>
          ) : (
            employees.map((emp, index) => (
              <TableRow
                key={emp.id}
                className={cn(
                  "cursor-pointer transition-colors",
                  selectedEmployee?.id === emp.id
                    ? "bg-primary/15 hover:bg-primary/20"
                    : index % 2 === 0
                    ? "bg-card hover:bg-accent"
                    : "bg-accent/40 hover:bg-accent"
                )}
                onClick={() => onSelect(emp)}
              >
                <TableCell className="text-center font-mono text-foreground">
                  {emp.id}
                </TableCell>
                <TableCell className="text-center text-foreground">{emp.firstName}</TableCell>
                <TableCell className="text-center text-foreground">{emp.lastName}</TableCell>
                <TableCell className="text-center text-foreground">{emp.startDate}</TableCell>
                <TableCell className="text-center font-semibold text-foreground">
                  {emp.leaveAvailable}
                </TableCell>
                <TableCell className="text-center font-semibold text-foreground">
                  {emp.sickLeaveAvailable}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
