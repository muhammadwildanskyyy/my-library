import DeskView from "@/components/desk/DeskView";

export default async function LibraryDeskPage({
  params,
}: {
  params: Promise<{ libraryId: string }>;
}) {
  const { libraryId } = await params;
  return <DeskView libraryId={libraryId} />;
}
