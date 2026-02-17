import { NextResponse } from "next/server";
import getDb from "@/lib/db";

// Helper to calculate leave balances (mirrors the Python logic)
function calculateLeaveBalances(
  employee: { id: string; firstName: string; lastName: string; startDate: string },
  annualLeaveRecords: { id: string; leaveTaken: number; leaveStart: string }[],
  sickLeaveRecords: { id: string; leaveTaken: number; leaveStart: string }[]
) {
  const now = new Date();

  // Parse start date (DD/MM/YYYY format)
  const parts = employee.startDate.split("/");
  const startDate = new Date(
    parseInt(parts[2]),
    parseInt(parts[1]) - 1,
    parseInt(parts[0])
  );

  // Calculate months difference
  const yearsDiff = now.getFullYear() - startDate.getFullYear();
  const monthsDiff = now.getMonth() - startDate.getMonth();
  const totalMonths = yearsDiff * 12 + monthsDiff;

  // Annual leave calculation (same as Python: 1.25 days per month, special case for 'sonja')
  let annualLeaveDays =
    employee.firstName.toLowerCase() === "sonja"
      ? totalMonths * (20 / 12)
      : totalMonths * 1.25;

  // Subtract leave already taken
  for (const leave of annualLeaveRecords) {
    if (leave.id === employee.id) {
      annualLeaveDays -= leave.leaveTaken;
    }
  }

  // Sick leave calculation (30-day cycle per 36 months)
  let allottedSickLeave = 30;
  const today = new Date();
  const empStartDate = new Date(
    parseInt(parts[2]),
    parseInt(parts[1]) - 1,
    parseInt(parts[0])
  );

  const deltaYears = today.getFullYear() - empStartDate.getFullYear();
  const deltaMonths = today.getMonth() - empStartDate.getMonth();
  const empTotalMonths = deltaYears * 12 + deltaMonths;

  if (empTotalMonths <= 6) {
    allottedSickLeave = empTotalMonths * 1;
  }

  // Get current 36-month cycle
  const currentCycle = Math.floor(empTotalMonths / 36);
  const startCycleDate = new Date(empStartDate);
  startCycleDate.setMonth(startCycleDate.getMonth() + currentCycle * 36);
  const endCycleDate = new Date(empStartDate);
  endCycleDate.setMonth(endCycleDate.getMonth() + (currentCycle + 1) * 36);

  let sickLeaveTaken = 0;
  for (const leave of sickLeaveRecords) {
    if (leave.id === employee.id && leave.leaveStart) {
      const leaveParts = leave.leaveStart.split("/");
      const leaveStartDate = new Date(
        parseInt(leaveParts[2]),
        parseInt(leaveParts[1]) - 1,
        parseInt(leaveParts[0])
      );
      if (leaveStartDate >= startCycleDate && leaveStartDate <= endCycleDate) {
        sickLeaveTaken += leave.leaveTaken;
      }
    }
  }

  return {
    ...employee,
    leaveAvailable: Math.round(annualLeaveDays * 100) / 100,
    sickLeaveAvailable: allottedSickLeave - sickLeaveTaken,
  };
}

export async function GET() {
  try {
    const db = getDb();

    const employees = db
      .prepare("SELECT * FROM employees ORDER BY firstName ASC")
      .all() as { id: string; firstName: string; lastName: string; startDate: string }[];

    const annualLeave = db
      .prepare("SELECT id, leaveTaken, leaveStart FROM annualLeave")
      .all() as { id: string; leaveTaken: number; leaveStart: string }[];

    const sickLeave = db
      .prepare("SELECT id, leaveTaken, leaveStart FROM sickLeave")
      .all() as { id: string; leaveTaken: number; leaveStart: string }[];

    const employeesWithLeave = employees.map((emp) =>
      calculateLeaveBalances(emp, annualLeave, sickLeave)
    );

    return NextResponse.json(employeesWithLeave);
  } catch (error) {
    console.error("Error fetching employees:", error);
    return NextResponse.json(
      { error: "Failed to fetch employees" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const db = getDb();
    const body = await request.json();
    const { id, firstName, lastName, startDate } = body;

    if (!id || !firstName || !lastName || !startDate) {
      return NextResponse.json(
        { error: "All fields are required" },
        { status: 400 }
      );
    }

    // Parse and reformat date to DD/MM/YYYY
    const formattedId = id.toUpperCase();
    const formattedFirstName =
      firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
    const formattedLastName =
      lastName.charAt(0).toUpperCase() + lastName.slice(1).toLowerCase();

    db.prepare(
      "INSERT INTO employees (id, firstName, lastName, startDate) VALUES (?, ?, ?, ?)"
    ).run(formattedId, formattedFirstName, formattedLastName, startDate);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error adding employee:", error);
    return NextResponse.json(
      { error: "Failed to add employee. ID may already exist." },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  try {
    const db = getDb();
    const body = await request.json();
    const { id, firstName, lastName, startDate } = body;

    if (!id) {
      return NextResponse.json(
        { error: "Employee ID is required" },
        { status: 400 }
      );
    }

    const formattedFirstName =
      firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
    const formattedLastName =
      lastName.charAt(0).toUpperCase() + lastName.slice(1).toLowerCase();

    db.prepare(
      "UPDATE employees SET firstName = ?, lastName = ?, startDate = ? WHERE id = ?"
    ).run(formattedFirstName, formattedLastName, startDate, id);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating employee:", error);
    return NextResponse.json(
      { error: "Failed to update employee" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  try {
    const db = getDb();
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json(
        { error: "Employee ID is required" },
        { status: 400 }
      );
    }

    db.prepare("DELETE FROM employees WHERE id = ?").run(id);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting employee:", error);
    return NextResponse.json(
      { error: "Failed to delete employee" },
      { status: 500 }
    );
  }
}
