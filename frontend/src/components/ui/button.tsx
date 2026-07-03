import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva('inline-flex h-9 items-center justify-center gap-2 rounded-md text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 disabled:pointer-events-none disabled:opacity-50', {
  variants: {
    variant: {
      default: 'bg-slate-950 text-white shadow-sm hover:bg-slate-800',
      secondary: 'border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50',
      ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-950',
      destructive: 'bg-red-600 text-white hover:bg-red-700',
    },
    size: { default: 'px-3', sm: 'h-8 px-2 text-xs', lg: 'h-10 px-4' },
  },
  defaultVariants: { variant: 'default', size: 'default' },
});

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild, children, ...props }, ref) => {
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<{ className?: string }>, {
      className: cn(buttonVariants({ variant, size }), (children as React.ReactElement<{ className?: string }>).props.className, className),
      ...props,
    });
  }
  return <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props}>{children}</button>;
});
Button.displayName = 'Button';
export { buttonVariants };
