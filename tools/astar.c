/* One-face octilinear A* for tools/pcbkit.py - the inner loop of pcbkit.Router, in C.

   Build (tools/pcbkit.py does this on first use, into tools/__pycache__):
       cc -O2 -shared -fPIC -o astar.so astar.c

   The grid is one copper face at 0.1 mm. cost[i] < 0 blocks a cell; otherwise entering it costs
   the step length times (1 + cost[i]). A step is one of eight directions; changing direction
   costs turn45 per 45 degrees and turns sharper than 90 degrees are not allowed, so every path
   is made of straight runs joined by 45 or 90 degree corners - the shapes drawn by hand. A
   diagonal step may not cut the corner of a blocked cell. Sources and goals are masks, so a
   route can leave from, or land on, any point of a net's existing copper.

   Returns the number of cells in the path written to out[] (as y * nx + x, source first), 0 if
   there is no path, -1 if out[] is too small. */
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct { float f; int s; } item;
typedef struct { item *a; int n, cap; } heap;

static void push(heap *h, float f, int s) {
    if (h->n == h->cap) { h->cap = h->cap ? h->cap * 2 : 1 << 16; h->a = realloc(h->a, h->cap * sizeof(item)); }
    int i = h->n++;
    while (i) { int p = (i - 1) / 2; if (h->a[p].f <= f) break; h->a[i] = h->a[p]; i = p; }
    h->a[i].f = f; h->a[i].s = s;
}

static item pop(heap *h) {
    item top = h->a[0], last = h->a[--h->n];
    int i = 0;
    for (;;) {
        int c = 2 * i + 1;
        if (c >= h->n) break;
        if (c + 1 < h->n && h->a[c + 1].f < h->a[c].f) c++;
        if (h->a[c].f >= last.f) break;
        h->a[i] = h->a[c]; i = c;
    }
    if (h->n) h->a[i] = last;
    return top;
}

static const int DX[8] = {1, 1, 0, -1, -1, -1, 0, 1};
static const int DY[8] = {0, 1, 1, 1, 0, -1, -1, -1};

int astar(int nx, int ny, const float *cost, const unsigned char *src, const unsigned char *goal,
          const float *hgrid, int x0, int y0, int x1, int y1, float turn45, const float *dirmul,
          int *out, int maxout) {
    int wx = x1 - x0 + 1, wy = y1 - y0 + 1;
    long ncell = (long)wx * wy, nst = ncell * 9;
    float *g = malloc(nst * sizeof(float));
    int *prev = malloc(nst * sizeof(int));
    unsigned char *closed = calloc(nst, 1);
    for (long i = 0; i < nst; i++) g[i] = 1e30f;
    heap h = {0};
    for (int y = y0; y <= y1; y++)
        for (int x = x0; x <= x1; x++) {
            int c = y * nx + x;
            if (!src[c]) continue;
            long s = ((long)(y - y0) * wx + (x - x0)) * 9 + 8;
            g[s] = 0; prev[s] = -1;
            push(&h, hgrid[c], (int)s);
        }
    long found = -1;
    while (h.n) {
        item it = pop(&h);
        long s = it.s;
        if (closed[s]) continue;
        closed[s] = 1;
        int d = (int)(s % 9);
        long cell = s / 9;
        int x = (int)(cell % wx) + x0, y = (int)(cell / wx) + y0;
        int c = y * nx + x;
        if (goal[c] && !src[c]) { found = s; break; }
        for (int k = 0; k < 8; k++) {
            float pen = 0;
            if (d < 8) {
                int dd = abs(k - d); if (dd > 4) dd = 8 - dd;
                if (dd > 2) continue;
                pen = turn45 * dd;
            }
            int X = x + DX[k], Y = y + DY[k];
            if (X < x0 || X > x1 || Y < y0 || Y > y1) continue;
            int C = Y * nx + X;
            if (cost[C] < 0) continue;
            if (DX[k] && DY[k] && (cost[y * nx + X] < 0 || cost[Y * nx + x] < 0)) continue;
            float step = ((DX[k] && DY[k]) ? 1.41421356f : 1.0f) * dirmul[k];
            float ng = g[s] + step * (1.0f + cost[C]) + pen;
            long S = ((long)(Y - y0) * wx + (X - x0)) * 9 + k;
            if (ng < g[S]) { g[S] = ng; prev[S] = (int)s; push(&h, ng + hgrid[C], (int)S); }
        }
    }
    int n = 0;
    if (found >= 0) {
        long s = found;
        while (s >= 0) { n++; s = prev[s]; }
        if (n > maxout) n = -1;
        else {
            int i = n; s = found;
            while (s >= 0) {
                long cell = s / 9;
                int x = (int)(cell % wx) + x0, y = (int)(cell / wx) + y0;
                out[--i] = y * nx + x;
                s = prev[s];
            }
        }
    }
    free(g); free(prev); free(closed); free(h.a);
    return n;
}
