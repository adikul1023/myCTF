/**
 * Next.js Middleware for authentication
 * Note: We use localStorage for JWT tokens, so auth checks happen client-side.
 * This middleware only handles basic routing.
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  // Let all requests through - auth is handled client-side
  // The dashboard and protected pages check for tokens in localStorage
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
