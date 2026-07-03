import * as React from 'react';
import { cn } from '../../lib/utils';
export const Table = React.forwardRef<HTMLTableElement, React.TableHTMLAttributes<HTMLTableElement>>(({ className, ...props }, ref) => <table ref={ref} className={cn('min-w-full border-separate border-spacing-0 text-left text-[13px]', className)} {...props} />);
export const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>((props, ref) => <thead ref={ref} {...props} />);
export const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>((props, ref) => <tbody ref={ref} {...props} />);
export const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(({ className, ...props }, ref) => <tr ref={ref} className={cn('hover:bg-slate-50', className)} {...props} />);
export const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(({ className, ...props }, ref) => <th ref={ref} className={cn('sticky top-0 z-10 border-b border-slate-200 bg-slate-50 px-3 py-2 font-semibold text-slate-500', className)} {...props} />);
export const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(({ className, ...props }, ref) => <td ref={ref} className={cn('border-b border-slate-100 px-3 py-2 text-slate-700', className)} {...props} />);
Table.displayName = 'Table'; TableHeader.displayName = 'TableHeader'; TableBody.displayName = 'TableBody'; TableRow.displayName = 'TableRow'; TableHead.displayName = 'TableHead'; TableCell.displayName = 'TableCell';
