import { NextRequest, NextResponse } from "next/server";

const PUBLIC_ROUTES = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes
  if (PUBLIC_ROUTES.some((r) => pathname.startsWith(r))) {
    return NextResponse.next();
  }

  // Check for auth token in cookies (set via Zustand persist → localStorage)
  // Since localStorage is client-side only, we check a cookie instead
  const token = request.cookies.get("ai_librarian_token")?.value;

  if (!pathname.startsWith("/api") && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all paths except:
     * - _next/static, _next/image (Next.js internals)
     * - favicon.ico
     * - API routes
     */
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
