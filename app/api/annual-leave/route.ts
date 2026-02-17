import { NextResponse } from "next/server";
import getDb from "@/lib/db";

export async function GET() {
  try {
    const db = getDb();
    const records = db
      .prepare("SELECT rowid, * FROM annualLeave ORDER BY id ASC")
      .all();
    return NextResponse.json(records);
  } catch (error) {
    console.error("Error fetching annual leave:", error);
    return NextResponse.json(
      { error: "Failed to fetch annual leave" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const db = getDb();
    const body = await request.json();
    const { id, firstName, leaveTaken, leaveStart, leaveEnd, comment } = body;

    if (!id || !leaveTaken || !leaveStart || !leaveEnd) {
      return NextResponse.json(
        { error: "ID, leave days, start date, and end date are required" },
        { status: 400 }
      );
    }

    db.prepare(
      "INSERT INTO annualLeave (id, firstName, leaveTaken, leaveStart, leaveEnd, comment) VALUES (?, ?, ?, ?, ?, ?)"
    ).run(id, firstName, parseFloat(leaveTaken), leaveStart, leaveEnd, comment || "");

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error adding annual leave:", error);
    return NextResponse.json(
      { error: "Failed to add annual leave" },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  try {
    const db = getDb();
    const body = await request.json();
    const { rowid, leaveTaken, leaveStart, leaveEnd, comment } = body;

    if (!rowid || !leaveTaken || !leaveStart || !leaveEnd) {
      return NextResponse.json(
        { error: "All fields are required" },
        { status: 400 }
      );
    }

    db.prepare(
      "UPDATE annualLeave SET leaveTaken = ?, leaveStart = ?, leaveEnd = ?, comment = ? WHERE rowid = ?"
    ).run(parseFloat(leaveTaken), leaveStart, leaveEnd, comment || "", rowid);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating annual leave:", error);
    return NextResponse.json(
      { error: "Failed to update annual leave" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  try {
    const db = getDb();
    const { searchParams } = new URL(request.url);
    const rowid = searchParams.get("rowid");

    if (!rowid) {
      return NextResponse.json(
        { error: "Row ID is required" },
        { status: 400 }
      );
    }

    db.prepare("DELETE FROM annualLeave WHERE rowid = ?").run(rowid);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting annual leave:", error);
    return NextResponse.json(
      { error: "Failed to delete annual leave" },
      { status: 500 }
    );
  }
}
