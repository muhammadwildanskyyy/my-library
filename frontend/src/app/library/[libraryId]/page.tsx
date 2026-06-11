import StacksView from "@/components/library/StacksView";

export default async function LibraryStacksPage({
  params,
}: {
  params: Promise<{ libraryId: string }>;
}) {
  const { libraryId } = await params;
  
  return <StacksView libraryId={libraryId} />;
}
