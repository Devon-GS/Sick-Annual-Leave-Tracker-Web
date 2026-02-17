"use client";

import { useState } from "react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";

interface LeaveEntry {
  days: number;
  start: string;
  end: string;
  comment: string;
}

interface EmployeeLeaveInfo {
  info: {
    firstName: string;
    lastName: string;
    startDate: string;
  };
  annual: LeaveEntry[];
  sick: LeaveEntry[];
}

interface ViewLeaveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function ViewLeaveDialog({ open, onOpenChange }: ViewLeaveDialogProps) {
  const { data } = useSWR<Record<string, EmployeeLeaveInfo>>(
    open ? "/api/view-leave" : null,
    fetcher
  );

  const employees = data ? Object.entries(data) : [];
  const [selectedTab, setSelectedTab] = useState<string>("");

  // Set default tab if not set
  if (employees.length > 0 && !selectedTab) {
    setSelectedTab(employees[0][0]);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto bg-card text-card-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">All Employee Leave Records</DialogTitle>
          <DialogDescription>
            View detailed leave information for each employee.
          </DialogDescription>
        </DialogHeader>

        {employees.length === 0 ? (
          <p className="text-center py-8 text-muted-foreground">
            No employee data available.
          </p>
        ) : (
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="flex flex-wrap h-auto gap-1">
              {employees.map(([empId, emp]) => (
                <TabsTrigger key={empId} value={empId} className="text-xs">
                  {emp.info.firstName} {emp.info.lastName}
                </TabsTrigger>
              ))}
            </TabsList>

            {employees.map(([empId, emp]) => (
              <TabsContent key={empId} value={empId} className="flex flex-col gap-6">
                {/* Employee Info */}
                <div className="rounded-lg border border-border p-4 bg-secondary/30">
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">ID</span>
                      <p className="font-mono font-semibold text-foreground">{empId}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">First Name</span>
                      <p className="font-semibold text-foreground">{emp.info.firstName}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Last Name</span>
                      <p className="font-semibold text-foreground">{emp.info.lastName}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Start Date</span>
                      <p className="font-semibold text-foreground">{emp.info.startDate}</p>
                    </div>
                  </div>
                </div>

                {/* Annual Leave */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-foreground">Annual Leave</h3>
                    <Badge variant="secondary">
                      {emp.annual.length} record{emp.annual.length !== 1 ? "s" : ""}
                    </Badge>
                  </div>
                  {emp.annual.length === 0 ? (
                    <p className="text-sm text-muted-foreground py-2">
                      No annual leave records.
                    </p>
                  ) : (
                    <div className="rounded-lg border border-border overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-primary/10 hover:bg-primary/10">
                            <TableHead className="text-foreground font-semibold text-center">Days</TableHead>
                            <TableHead className="text-foreground font-semibold text-center">Start</TableHead>
                            <TableHead className="text-foreground font-semibold text-center">End</TableHead>
                            <TableHead className="text-foreground font-semibold">Comment</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {emp.annual.map((leave, i) => (
                            <TableRow key={i}>
                              <TableCell className="text-center text-foreground">{leave.days}</TableCell>
                              <TableCell className="text-center text-foreground">{leave.start}</TableCell>
                              <TableCell className="text-center text-foreground">{leave.end}</TableCell>
                              <TableCell className="text-foreground">{leave.comment}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>

                {/* Sick Leave */}
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-foreground">Sick Leave</h3>
                    <Badge variant="secondary">
                      {emp.sick.length} record{emp.sick.length !== 1 ? "s" : ""}
                    </Badge>
                  </div>
                  {emp.sick.length === 0 ? (
                    <p className="text-sm text-muted-foreground py-2">
                      No sick leave records.
                    </p>
                  ) : (
                    <div className="rounded-lg border border-border overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-primary/10 hover:bg-primary/10">
                            <TableHead className="text-foreground font-semibold text-center">Days</TableHead>
                            <TableHead className="text-foreground font-semibold text-center">Start</TableHead>
                            <TableHead className="text-foreground font-semibold text-center">End</TableHead>
                            <TableHead className="text-foreground font-semibold">Comment</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {emp.sick.map((leave, i) => (
                            <TableRow key={i}>
                              <TableCell className="text-center text-foreground">{leave.days}</TableCell>
                              <TableCell className="text-center text-foreground">{leave.start}</TableCell>
                              <TableCell className="text-center text-foreground">{leave.end}</TableCell>
                              <TableCell className="text-foreground">{leave.comment}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
