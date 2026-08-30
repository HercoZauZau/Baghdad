import { useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";

const EXPRESSIONS = {
  neutral: {},

  happy: {
    mouthSmileLeft: 0.65,
    mouthSmileRight: 0.65,
    cheekSquintLeft: 0.2,
    cheekSquintRight: 0.2,
  },

  surprised: {
    browInnerUp: 0.6,
    browOuterUpLeft: 0.4,
    browOuterUpRight: 0.4,
    eyeWideLeft: 0.3,
    eyeWideRight: 0.3,
    jawOpen: 0.3,
    mouthFunnel: 0.15,
  },

  thinking: {
    browInnerUp: 0.15,
    browDownLeft: 0.2,
    mouthPressLeft: 0.15,
    mouthPressRight: 0.15,
  },
};

const EXPRESSION_TARGETS = [
  "mouthSmileLeft",
  "mouthSmileRight",
  "cheekSquintLeft",
  "cheekSquintRight",

  "browInnerUp",
  "browOuterUpLeft",
  "browOuterUpRight",
  "browDownLeft",

  "eyeWideLeft",
  "eyeWideRight",

  "jawOpen",
  "mouthFunnel",

  "mouthPressLeft",
  "mouthPressRight",
];

export default function Avatar({ expression = "neutral" }) {
  const { scene } = useGLTF("/models/baghdad.glb");

  const morphMeshes = useRef([]);
  const blinkTargets = useRef([]);

  const head = useRef(null);
  const neck = useRef(null);
  const spine = useRef(null);

  const nextBlink = useRef(2);
  const blinkStart = useRef(null);

  useEffect(() => {
    morphMeshes.current = [];
    blinkTargets.current = [];

    scene.traverse((object) => {
      if (object.morphTargetDictionary) {
        morphMeshes.current.push(object);

        const dictionary = object.morphTargetDictionary;

        const leftIndex = dictionary.eyeBlinkLeft;
        const rightIndex = dictionary.eyeBlinkRight;

        if (
          leftIndex !== undefined ||
          rightIndex !== undefined
        ) {
          blinkTargets.current.push({
            object,
            leftIndex,
            rightIndex,
          });
        }
      }

      if (object.isBone) {
        if (object.name === "Head") {
          head.current = object;
        }

        if (object.name === "Neck") {
          neck.current = object;
        }

        if (object.name === "Spine2") {
          spine.current = object;
        }
      }
    });
  }, [scene]);

  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();

    /*
     * EXPRESSÕES
     */

    const currentExpression =
      EXPRESSIONS[expression] || EXPRESSIONS.neutral;

    morphMeshes.current.forEach((object) => {
      const dictionary = object.morphTargetDictionary;
      const influences = object.morphTargetInfluences;

      EXPRESSION_TARGETS.forEach((name) => {
        const index = dictionary[name];

        if (index === undefined) return;

        const target = currentExpression[name] || 0;

        influences[index] = THREE.MathUtils.lerp(
          influences[index],
          target,
          0.12
        );
      });
    });

    /*
     * PISCAR
     */

    if (
      blinkStart.current === null &&
      time >= nextBlink.current
    ) {
      blinkStart.current = time;
    }

    let blink = 0;

    if (blinkStart.current !== null) {
      const elapsed = time - blinkStart.current;
      const duration = 0.22;

      if (elapsed < duration / 2) {
        blink = elapsed / (duration / 2);
      } else if (elapsed < duration) {
        blink =
          1 -
          (elapsed - duration / 2) /
            (duration / 2);
      } else {
        blink = 0;
        blinkStart.current = null;

        nextBlink.current =
          time + 2.5 + Math.random() * 3.5;
      }
    }

    blinkTargets.current.forEach(
      ({ object, leftIndex, rightIndex }) => {
        if (leftIndex !== undefined) {
          object.morphTargetInfluences[leftIndex] =
            blink;
        }

        if (rightIndex !== undefined) {
          object.morphTargetInfluences[rightIndex] =
            blink;
        }
      }
    );

    /*
     * RESPIRAÇÃO
     */

    if (spine.current) {
      spine.current.rotation.x =
        Math.sin(time * 1.2) * 0.008;
    }

    /*
     * CABEÇA
     */

    if (head.current) {
      head.current.rotation.y =
        Math.sin(time * 0.35) * 0.025;

      head.current.rotation.x =
        Math.sin(time * 0.23) * 0.012;
    }

    /*
     * PESCOÇO
     */

    if (neck.current) {
      neck.current.rotation.z =
        Math.sin(time * 0.3) * 0.008;
    }
  });

  return (
    <primitive
      object={scene}
      position={[0, 0, 0]}
      scale={1}
    />
  );
}

useGLTF.preload("/models/baghdad.glb");