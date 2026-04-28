'use client';

import { useEffect } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

export function GsapInitializer() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);

    // Fade up animations
    const fadeElements = gsap.utils.toArray('.animate-fade-up') as HTMLElement[];
    fadeElements.forEach((el) => {
      gsap.fromTo(
        el,
        { y: 60, opacity: 0 },
        {
          scrollTrigger: {
            trigger: el,
            start: 'top 85%',
          },
          y: 0,
          opacity: 1,
          duration: 0.9,
          ease: 'power3.out',
        }
      );
    });

    // Staggered reveals
    const staggerContainers = gsap.utils.toArray('.animate-stagger-container') as HTMLElement[];
    staggerContainers.forEach((container) => {
      const children = Array.from(container.children);
      gsap.fromTo(
        children,
        { y: 40, opacity: 0 },
        {
          scrollTrigger: {
            trigger: container,
            start: 'top 85%',
          },
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
        }
      );
    });
    
    // 3D Parallax floating
    const floatElements = gsap.utils.toArray('.animate-float-3d') as HTMLElement[];
    floatElements.forEach((el) => {
      gsap.to(el, {
        y: '-=20',
        rotateX: '+=2',
        rotateY: '-=2',
        duration: 2.5,
        yoyo: true,
        repeat: -1,
        ease: 'sine.inOut',
      });
    });

    return () => {
      ScrollTrigger.getAll().forEach(t => t.kill());
    };
  }, []);

  return null;
}
