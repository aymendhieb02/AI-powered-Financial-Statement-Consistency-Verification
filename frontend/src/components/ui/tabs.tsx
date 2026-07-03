import * as TabsPrimitive from '@radix-ui/react-tabs';
import { cn } from '../../lib/utils';
export const Tabs = TabsPrimitive.Root;
export const TabsList = ({ className, ...props }: TabsPrimitive.TabsListProps) => <TabsPrimitive.List className={cn('flex gap-1 border-b border-slate-200', className)} {...props} />;
export const TabsTrigger = ({ className, ...props }: TabsPrimitive.TabsTriggerProps) => <TabsPrimitive.Trigger className={cn('px-3 py-2 text-sm font-medium text-slate-500 transition data-[state=active]:border-b-2 data-[state=active]:border-slate-950 data-[state=active]:text-slate-950 hover:text-slate-900', className)} {...props} />;
export const TabsContent = TabsPrimitive.Content;
