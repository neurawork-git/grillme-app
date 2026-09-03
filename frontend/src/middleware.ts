import { NextResponse, type NextRequest } from "next/server";

// Clientseitiger Fallback zur 401-Antwort des Backends: kein Session-Cookie -> Login.
// Starlettes SessionMiddleware setzt den Cookie standardmäßig als "session".
export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has("session");

  if (!hasSession && request.nextUrl.pathname.startsWith("/sessions")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/sessions/:path*"],
};
