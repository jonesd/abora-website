/*
 * Abora-Website
 * Part of the Abora hypertext project: http://www.abora.org
 * Copyright 2003 David G Jones
 */
package org.abora.website.tools;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;

public class RecentMarkers {
	private final DateFormat format; 
	private final Date lastWeek;
	private final Date lastMonth;

	// Match text in the source that indicates date of modification
	private static final String MATCH_SOURCE_DATE_START = "<!--modified:";
	private static final String MATCH_SOURCE_DATE_END = "-->";

	// CSS class used to mark age of modification date
	private static final String MODIFIED_LONG_AGO = "modified-long-ago";
	private static final String MODIFIED_LAST_MONTH = "modified-last-month";
	private static final String MODIFIED_LAST_WEEK = "modified-last-week";

	public static void main(String[] args) {
		if (args.length != 1) {
			System.err.println("Usage: <htmlFileName>");
			System.exit(1);
		}
		String filename = args[0];
		
		try {
			new RecentMarkers().process(filename);		
		} catch (Exception e) {
			e.printStackTrace();
			System.exit(2);
		}
	}
	
	public RecentMarkers() {
		format = new SimpleDateFormat("yyyyMMdd");

		Calendar lastWeekCalendar = Calendar.getInstance();
		lastWeekCalendar.add(Calendar.DAY_OF_YEAR, -7);
		lastWeek = lastWeekCalendar.getTime();

		Calendar lastMonthCalendar = Calendar.getInstance();
		lastMonthCalendar.add(Calendar.DAY_OF_YEAR, -30);
		lastMonth = lastMonthCalendar.getTime();
	}
	
	public void process(String filename) throws Exception {
		String contents = readFile(filename);
		char[] contentsChar = contents.toCharArray();
		StringBuffer buffer = new StringBuffer(contents.length());
		int last = 0;
		int next;
		while ((next = contents.indexOf(MATCH_SOURCE_DATE_START, last)) != -1) {
			int end = contents.indexOf(MATCH_SOURCE_DATE_END, next);
			if (end == -1) {
				throw new IllegalStateException("Couldn't interpret text at: "+next);
			}
			String date = contents.substring(next+MATCH_SOURCE_DATE_START.length(), end);
			buffer.append(contentsChar, last, next - last);
			buffer.append("<span class=\"");
			buffer.append(cssClassForDate(date));
			buffer.append("\">");
			buffer.append(date);
			buffer.append("</span>");
			last = end + MATCH_SOURCE_DATE_END.length();
		}
		buffer.append(contentsChar, last, contentsChar.length - last);
		writeFile(filename, buffer);
	}
	
	private String cssClassForDate(String date) throws ParseException {
		Date parsedDate = format.parse(date);
		
		if (parsedDate.after(lastWeek)) {
			return MODIFIED_LAST_WEEK;
		} else if (parsedDate.after(lastMonth)) {
			return MODIFIED_LAST_MONTH;
		} else {
			return MODIFIED_LONG_AGO;
		}
	}

	private String readFile(String filename) throws IOException {
		StringBuffer buffer = new StringBuffer();
		BufferedReader reader = new BufferedReader(new FileReader(filename));
		try {
			String line;
			while((line = reader.readLine()) != null) {
				buffer.append(line);
				buffer.append('\n');
			}
		} finally {
			reader.close();
		}
		return buffer.toString();
	}
	
	private void writeFile(String filename, StringBuffer buffer) throws IOException {
		BufferedWriter writer = new BufferedWriter(new FileWriter(filename));
		try {
			writer.write(buffer.toString());
		} finally {
			writer.close();
		}
	}
}
