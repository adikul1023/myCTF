# Investigation Portal - Frontend

A minimal, professional frontend for a Digital Forensics and Incident Response (DFIR) training platform. This interface is designed to feel like an internal investigation tool - no gamification, no distractions, just the evidence and the work.

## Design Philosophy

### The Investigation Aesthetic

This frontend embodies the serious, focused nature of digital forensics work:

- **No Gamification**: No badges, achievements, leaderboards, or celebration animations
- **No Colors**: Pure grayscale palette - cold, professional, unadorned
- **No Animations**: Zero transition effects - information appears instantly
- **Typography First**: Monospace fonts, clear hierarchy, proper whitespace
- **Serious Tone**: You're not "playing a game", you're reviewing case files

### Visual Language

- Feels like opening a sealed envelope marked "CONFIDENTIAL"
- Interface is a tool, not an experience
- Assumes user competence - minimal hand-holding
- Information density over visual flair
- Every pixel serves a purpose

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Authentication**: JWT with http-only cookies
- **API**: REST API at http://localhost:8002

## Project Structure

```
frontend/
├── app/
│   ├── admin/              # Admin panel (case management)
│   │   └── page.tsx
│   ├── cases/              # Case detail pages
│   │   └── [id]/
│   │       └── page.tsx
│   ├── dashboard/          # Main dashboard (case list)
│   │   └── page.tsx
│   ├── login/              # Authentication
│   │   └── page.tsx
│   ├── register/           # User registration
│   │   └── page.tsx
│   ├── globals.css         # Investigation Portal theme
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Home (redirects to dashboard)
├── lib/
│   ├── api.ts              # API client
│   └── auth.ts             # Auth utilities
└── middleware.ts           # Route protection
```

## Setup

### Prerequisites

- Node.js 20+
- Backend API running at http://localhost:8002

### Installation

```bash
# Install dependencies
npm install

# Configure environment
# Edit .env.local if your backend runs on a different port
# Default: NEXT_PUBLIC_API_URL=http://localhost:8002

# Start development server
npm run dev
```

Open http://localhost:3000

### First Time Setup

1. Register a new account at `/register`
2. Login at `/login`
3. View available cases at `/dashboard`
4. Open a case to see evidence and challenges

## Features

### Authentication

- JWT-based authentication with http-only cookies
- Invite code support for registration
- Session management
- Route protection middleware

### Dashboard

- List of available investigation cases
- Progress tracking (challenges solved, points earned)
- Minimal, file-system-like interface
- No visual noise or distractions

### Case View

- Case narrative/brief
- Evidence file downloads
- Challenge submission interface
- Real-time progress updates
- Clean, document-like presentation

### Admin Panel

- Create new cases
- Manage case visibility
- View all cases (active/inactive)
- Upload artifacts (via API)

## Design System

### Color Palette

All colors are grayscale - no hues:

- `investigation-bg`: #0a0a0a (background)
- `investigation-surface`: #141414 (cards, inputs)
- `investigation-border`: #262626 (dividers)
- `investigation-text`: #e5e5e5 (primary text)
- `investigation-muted`: #737373 (secondary text)
- `investigation-accent`: #525252 (hover states)

### Typography

- **Primary Font**: Monospace (JetBrains Mono, Courier New)
- **Fallback**: Inter, system sans-serif
- **Sizes**: 12px-24px (small, functional)
- **Style**: Uppercase headings with letter-spacing

### Component Classes

```css
.investigation-input     /* Form inputs */
.investigation-button    /* Buttons */
.investigation-card      /* Content containers */
.investigation-heading   /* Section headings */
```

### UI Principles

1. **No Transitions**: All CSS transitions/animations disabled
2. **Functional First**: Every element serves a purpose
3. **Consistent Spacing**: 1rem base unit
4. **Monospace Everywhere**: Code/terminal aesthetic
5. **Minimal Borders**: Subtle dividers, no shadows

## API Integration

The frontend communicates with the backend at `NEXT_PUBLIC_API_URL`:

### Endpoints Used

- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Authenticate
- `POST /api/auth/logout` - Sign out
- `GET /api/auth/me` - Get current user
- `GET /api/cases` - List cases
- `GET /api/cases/:id` - Case details
- `GET /api/cases/:id/artifacts` - Evidence files
- `GET /api/challenges?case_id=:id` - Case challenges
- `POST /api/submissions` - Submit flag
- `GET /api/submissions?case_id=:id` - User progress

### Authentication Flow

1. User logs in via `/login`
2. Backend sets http-only `session` cookie
3. Middleware checks cookie on protected routes
4. API client includes `credentials: 'include'` in all requests
5. Backend validates JWT on each request

## Development

### Running Locally

```bash
# Development mode with hot reload
npm run dev

# Production build
npm run build
npm start

# Lint
npm run lint
```

### Code Style

- **TypeScript**: Strict mode enabled
- **Naming**: camelCase for variables, PascalCase for components
- **Components**: Functional components with hooks
- **State**: useState for local, useEffect for side effects
- **Async**: async/await pattern

### Adding New Pages

1. Create page in `app/` directory
2. Add route protection in `middleware.ts` if needed
3. Use investigation design system classes
4. Follow minimal, professional aesthetic

## Production Deployment

### Environment Variables

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Build

```bash
npm run build
```

Outputs optimized production build to `.next/`

### Hosting

Can deploy to:
- Vercel (recommended for Next.js)
- Docker container
- Any Node.js hosting platform

## Troubleshooting

### "Network Error" on API calls

- Check backend is running at `http://localhost:8002`
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check browser console for CORS errors

### Redirected to /login constantly

- Check browser cookies (need http-only `session` cookie)
- Verify backend JWT is working
- Check middleware.ts configuration

### Styles not applying

- Ensure `globals.css` is imported in `layout.tsx`
- Check Tailwind v4 PostCSS config
- Verify CSS custom properties are defined

## Design Decisions

### Why No Animations?

Animations suggest entertainment. This is work. Information should appear instantly, like reading a document.

### Why Grayscale?

Color implies emotion and urgency. Digital forensics requires cold, methodical analysis without emotional influence.

### Why Monospace?

Monospace fonts evoke terminals, code, and technical work. They create visual consistency and a serious, professional tone.

### Why No Gamification?

Real investigations don't have progress bars and achievement unlocks. This platform trains professionals, not entertains players.

---

**Remember**: This interface is a tool for serious work. Every design choice reinforces that this is an investigation, not a game.

