<?php
declare(strict_types=1);

$title = 'Neko bajo la Vía Láctea';
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#050624">
    <title><?= htmlspecialchars($title, ENT_QUOTES, 'UTF-8') ?></title>
    <style>
        :root { color-scheme: dark; }
        * { box-sizing: border-box; }
        html, body { width: 100%; min-height: 100%; margin: 0; }
        body {
            min-height: 100svh;
            display: grid;
            place-items: center;
            overflow: hidden;
            background: #02020d;
        }
        .scene {
            position: relative;
            height: 100svh;
            max-width: 100vw;
            aspect-ratio: 864 / 1242;
            overflow: hidden;
            isolation: isolate;
            background: #070828;
            box-shadow: 0 0 80px #35187566;
        }
        .background {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            user-select: none;
            pointer-events: none;
        }
        #effects {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            z-index: 2;
            pointer-events: none;
        }
        .tail {
            position: absolute;
            z-index: 3;
            left: 47.1%;
            top: 66.15%;
            width: 3.3%;
            height: 3.5%;
            transform-origin: 80% 82%;
            animation: wag 1.65s ease-in-out infinite alternate;
            filter: drop-shadow(-1px 1px 0 #171323) drop-shadow(1px 0 0 #171323);
        }
        .tail::before {
            content: '';
            position: absolute;
            inset: 0;
            border: clamp(2px, .42vw, 5px) solid #b8b7ca;
            border-right-color: transparent;
            border-top-color: transparent;
            border-radius: 50%;
            transform: rotate(-25deg);
            box-shadow: inset 2px -1px 0 #83879f;
        }
        .tail::after {
            content: '';
            position: absolute;
            left: 2%;
            top: 9%;
            width: 31%;
            aspect-ratio: 1;
            border-radius: 2px;
            background: #d1ceda;
        }
        .glow {
            position: absolute;
            inset: 0;
            z-index: 4;
            pointer-events: none;
            background:
                radial-gradient(circle at 48% 40%, #aa71ff12 0 18%, transparent 42%),
                linear-gradient(180deg, transparent 68%, #03041222 100%);
            mix-blend-mode: screen;
        }
        @keyframes wag {
            0% { transform: rotate(-13deg) translate(-1px, 0); }
            50% { transform: rotate(1deg) translate(0, -1px); }
            100% { transform: rotate(18deg) translate(2px, 0); }
        }
        @media (max-aspect-ratio: 864 / 1242) {
            .scene { width: 100vw; height: auto; }
        }
        @media (prefers-reduced-motion: reduce) {
            .tail { animation: none; }
        }
    </style>
</head>
<body>
<main class="scene" aria-label="Gato contemplando una Vía Láctea animada">
    <img class="background" src="assets/galaxy-neko.jpg" alt="Gato con audífonos contemplando la Vía Láctea desde una colina">
    <canvas id="effects" width="432" height="621" aria-hidden="true"></canvas>
    <span class="tail" aria-hidden="true"></span>
    <div class="glow" aria-hidden="true"></div>
</main>

<script>
(() => {
    'use strict';

    const canvas = document.querySelector('#effects');
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const skyLimit = 408;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

    let seed = 28471;
    const random = () => ((seed = seed * 16807 % 2147483647) - 1) / 2147483646;

    const stars = Array.from({ length: 90 }, (_, index) => ({
        x: random() * W,
        y: random() * skyLimit,
        radius: index < 14 ? 1.25 + random() * 1.2 : .45 + random() * .75,
        phase: random() * Math.PI * 2,
        speed: .65 + random() * 2.1,
        drift: .08 + random() * .2,
        hue: random() > .62 ? '226,216,255' : '255,255,255'
    }));

    const dust = Array.from({ length: 55 }, () => ({
        x: 112 + random() * 155,
        y: random() * 385,
        phase: random() * Math.PI * 2,
        speed: .35 + random() * .7
    }));

    function drawStars(time) {
        for (const star of stars) {
            const pulse = .16 + ((Math.sin(time * star.speed + star.phase) + 1) / 2) * .74;
            const y = reduced ? star.y : (star.y + time * star.drift) % skyLimit;
            ctx.fillStyle = `rgba(${star.hue},${pulse})`;
            ctx.beginPath();
            ctx.arc(star.x, y, star.radius, 0, Math.PI * 2);
            ctx.fill();

            if (star.radius > 1.55 && pulse > .63) {
                ctx.fillStyle = `rgba(225,218,255,${(pulse - .5) * .72})`;
                ctx.fillRect(Math.round(star.x) - 4, Math.round(y), 9, 1);
                ctx.fillRect(Math.round(star.x), Math.round(y) - 4, 1, 9);
            }
        }
    }

    function drawGalaxyDust(time) {
        for (const point of dust) {
            const alpha = .08 + ((Math.sin(time * point.speed + point.phase) + 1) / 2) * .3;
            ctx.fillStyle = `rgba(221,168,255,${alpha})`;
            ctx.fillRect(Math.round(point.x), Math.round(point.y), 1, 1);
        }
    }

    function drawShootingStar(time, offset, startX, startY) {
        const duration = 1.35;
        const wait = 7.8;
        const cycle = (time + offset) % wait;
        if (cycle > duration || reduced) return;

        const p = cycle / duration;
        const fade = Math.sin(p * Math.PI);
        const x = startX + p * 145;
        const y = startY + p * 61;

        ctx.save();
        ctx.globalAlpha = fade;
        ctx.lineCap = 'round';
        const gradient = ctx.createLinearGradient(x - 62, y - 26, x, y);
        gradient.addColorStop(0, 'rgba(151,104,255,0)');
        gradient.addColorStop(.65, 'rgba(207,186,255,.55)');
        gradient.addColorStop(1, '#fff');
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x - 62, y - 26);
        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(x, y, 1.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    function frame(ms) {
        const time = ms / 1000;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawGalaxyDust(reduced ? 1 : time);
        drawStars(reduced ? 1 : time);
        drawShootingStar(time, 0, -45, 82);
        drawShootingStar(time, 4.4, 210, 35);
        requestAnimationFrame(frame);
    }

    requestAnimationFrame(frame);
})();
</script>
</body>
</html>
