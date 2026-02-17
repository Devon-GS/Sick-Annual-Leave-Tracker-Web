import { NextResponse } from "next/server";
import getDb from "@/lib/db";

export async function GET() {
  try {
    const db = getDb();

    const employees = db.prepare("SELECT * FROM employees ORDER BY firstName ASC").all() as {
      id: string;
      firstName: string;
      lastName: string;
      startDate: string;
    }[];

    const annualLeave = db.prepare("SELECT * FROM annualLeave ORDER BY leaveStart ASC").all() as {
      id: string;
      firstName: string;
      leaveTaken: number;
      leaveStart: string;
      leaveEnd: string;
      comment: string;
    }[];

    const sickLeave = db.prepare("SELECT * FROM sickLeave ORDER BY leaveStart ASC").all() as {
      id: string;
      firstName: string;
      leaveTaken: number;
      leaveStart: string;
      leaveEnd: string;
      comment: string;
    }[];

    // Build employee info dictionary like the Python version
    const empInfo: Record<
      string,
      {
        info: { firstName: string; lastName: string; startDate: string };
        annual: { days: number; start: string; end: string; comment: string }[];
        sick: { days: number; start: string; end: string; comment: string }[];
      }
    > = {};

    for (const emp of employees) {
      empInfo[emp.id] = {
        info: {
          firstName: emp.firstName,
          lastName: emp.lastName,
          startDate: emp.startDate,
        },
        annual: [],
        sick: [],
      };
    }

    for (const al of annualLeave) {
      if (empInfo[al.id]) {
        empInfo[al.id].annual.push({
          days: al.leaveTaken,
          start: al.leaveStart,
          end: al.leaveEnd,
          comment: al.comment,
        });
      }
    }

    for (const sl of sickLeave) {
      if (empInfo[sl.id]) {
        empInfo[sl.id].sick.push({
          days: sl.leaveTaken,
          start: sl.leaveStart,
          end: sl.leaveEnd,
          comment: sl.comment,
        });
      }
    }

    return NextResponse.json(empInfo);
  } catch (error) {
    console.error("Error fetching leave data:", error);
    return NextResponse.json(
      { error: "Failed to fetch leave data" },
      { status: 500 }
    );
  }
}
