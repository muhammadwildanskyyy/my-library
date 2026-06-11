import DeskView from "@/components/desk/DeskView";

export default async function BookDeskPage({
  params,
}: {
  params: Promise<{ libraryId: string; bookId: string }>;
}) {
  const { libraryId, bookId } = await params;
  
  return <DeskView libraryId={libraryId} bookId={bookId} />;
}
