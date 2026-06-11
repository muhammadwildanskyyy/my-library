import ShelfView from "@/components/library/ShelfView";

export default async function ShelfPage({
  params,
}: {
  params: Promise<{ libraryId: string; shelfId: string }>;
}) {
  const { libraryId, shelfId } = await params;
  return <ShelfView libraryId={libraryId} shelfId={shelfId} />;
}
