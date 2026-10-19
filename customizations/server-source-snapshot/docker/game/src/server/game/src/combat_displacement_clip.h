#ifndef CUSTOM_COMBAT_DISPLACEMENT_CLIP_H
#define CUSTOM_COMBAT_DISPLACEMENT_CLIP_H
#include <cmath>
#include <algorithm>
// CUSTOM_COMBAT_WALL_SYNC_V1: traverse every collision cell, including corners.
// Blocked receives cell-centre coordinates; all arithmetic supports negative maps.
template <typename Blocked>
inline bool ClipCombatDisplacement(long sx, long sy, long& tx, long& ty, Blocked blocked)
{
    const long requestedX = tx, requestedY = ty;
    const double dx = double(tx) - sx, dy = double(ty) - sy;
    if (dx == 0 && dy == 0) return false;
    const long cell = 50;
    long cx = long(std::floor(double(sx) / cell));
    long cy = long(std::floor(double(sy) / cell));
    const long ex = long(std::floor(double(tx) / cell));
    const long ey = long(std::floor(double(ty) / cell));
    const int stepx = dx > 0 ? 1 : (dx < 0 ? -1 : 0);
    const int stepy = dy > 0 ? 1 : (dy < 0 ? -1 : 0);
    const double infinity = 1e100;
    double nx = stepx ? ((cx + (stepx > 0 ? 1 : 0)) * cell - sx) / dx : infinity;
    double ny = stepy ? ((cy + (stepy > 0 ? 1 : 0)) * cell - sy) / dy : infinity;
    const double incx = stepx ? cell / std::fabs(dx) : infinity;
    const double incy = stepy ? cell / std::fabs(dy) : infinity;
    double hit = -1;
    // An already blocked spawn may leave its current cell; never enter another blocked cell.
    while (cx != ex || cy != ey)
    {
        const double t = std::min(nx, ny);
        if (t > 1) break;
        if (std::fabs(nx - ny) < 1e-10)
        {
            if (blocked((cx + stepx) * cell + cell / 2, cy * cell + cell / 2) ||
                blocked(cx * cell + cell / 2, (cy + stepy) * cell + cell / 2) ||
                blocked((cx + stepx) * cell + cell / 2, (cy + stepy) * cell + cell / 2))
            { hit = t; break; }
            cx += stepx; cy += stepy; nx += incx; ny += incy;
        }
        else if (nx < ny)
        {
            if (blocked((cx + stepx) * cell + cell / 2, cy * cell + cell / 2))
            { hit = t; break; }
            cx += stepx; nx += incx;
        }
        else
        {
            if (blocked(cx * cell + cell / 2, (cy + stepy) * cell + cell / 2))
            { hit = t; break; }
            cy += stepy; ny += incy;
        }
    }
    if (hit >= 0)
    {
        const double safe = std::max(0.0, hit - 2.0 / std::max(std::fabs(dx), std::fabs(dy)));
        tx = long(std::floor(sx + dx * safe));
        ty = long(std::floor(sy + dy * safe));
    }
    return tx != requestedX || ty != requestedY;
}
#endif
