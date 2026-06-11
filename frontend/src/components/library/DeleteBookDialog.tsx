"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Loader2 } from "lucide-react";

interface DeleteBookDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
  isDeleting?: boolean;
  title?: string;
  bookName?: string;
}

export function DeleteBookDialog({
  open,
  onOpenChange,
  onConfirm,
  isDeleting,
  title = "Delete Book",
  bookName,
}: DeleteBookDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md border-rose-900/30">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 bg-rose-500/10 text-rose-600 rounded-full flex-shrink-0">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <DialogTitle className="text-xl">{title}</DialogTitle>
          </div>
          <DialogDescription className="text-base mt-2">
            Are you sure you want to delete{" "}
            {bookName ? <strong className="text-foreground font-semibold">"{bookName}"</strong> : "this book"}?
            This action cannot be undone and will permanently remove the document from your library.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="mt-4 gap-3 sm:gap-3">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isDeleting}
            className="bg-rose-600 hover:bg-rose-700 text-white border-none shadow shadow-rose-900/20"
          >
            {isDeleting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              "Yes, Delete Book"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
