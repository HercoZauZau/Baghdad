import { useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import {
  useAnimations,
  useGLTF,
} from "@react-three/drei";

import * as THREE from "three";


/*
 * EXPRESSÕES FACIAIS
 */

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


/*
 * MORPH TARGETS USADOS PELAS EXPRESSÕES
 */

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


export default function Avatar({
  expression = "neutral",
}) {

  /*
   * CARREGAR AVATAR
   */

  const {
    scene,
    animations,
  } = useGLTF(
    "/models/baghdad_idle_v2.glb"
  );


  /*
   * ANIMAÇÕES CORPORAIS
   */

  const {
    actions,
  } = useAnimations(
    animations,
    scene
  );


  /*
   * MESHES COM MORPH TARGETS
   */

  const morphMeshes =
    useRef([]);


  /*
   * MESHES QUE CONTROLAM O PISCAR
   */

  const blinkTargets =
    useRef([]);


  /*
   * CONTROLO DO PISCAR
   */

  const nextBlink =
    useRef(2);

  const blinkStart =
    useRef(null);


  /*
   * INSPECCIONAR AVATAR
   */

  useEffect(() => {

    morphMeshes.current = [];

    blinkTargets.current = [];


    scene.traverse((object) => {

      /*
       * IGNORAR OBJECTOS SEM MORPH TARGETS
       */

      if (
        !object.morphTargetDictionary
      ) {
        return;
      }


      /*
       * GUARDAR MESH
       */

      morphMeshes.current.push(
        object
      );


      const dictionary =
        object.morphTargetDictionary;


      /*
       * =====================================
       * PROCURAR VISEMES
       * =====================================
       */

      const morphNames =
        Object.keys(
          dictionary
        );


      const visemes =
        morphNames.filter(
          (name) =>
            name
              .toLowerCase()
              .includes("viseme")
        );


      if (
        visemes.length > 0
      ) {

        console.log(
          "VISEMES:",
          object.name,
          visemes
        );

      }


      /*
       * =====================================
       * PROCURAR BLINK
       * =====================================
       */

      const leftIndex =
        dictionary.eyeBlinkLeft;

      const rightIndex =
        dictionary.eyeBlinkRight;


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

    });


    /*
     * INFORMAÇÃO DE DEBUG
     */

    console.log(
      "Animações:",
      animations
    );

  }, [
    scene,
    animations,
  ]);


  /*
   * =====================================
   * TOCAR IDLE
   * =====================================
   */

  useEffect(() => {

    const idle =
      actions[
        "Female_Animation_Idle"
      ];


    if (!idle) {

      console.warn(
        "Female_Animation_Idle não encontrada."
      );

      return;

    }


    idle.reset();

    idle.fadeIn(0.5);

    idle.play();


    return () => {

      idle.fadeOut(0.5);

    };

  }, [actions]);


  /*
   * =====================================
   * LOOP PRINCIPAL
   * =====================================
   */

  useFrame(({ clock }) => {

    const time =
      clock.getElapsedTime();


    /*
     * =====================================
     * EXPRESSÕES FACIAIS
     * =====================================
     */

    const currentExpression =
      EXPRESSIONS[expression] ||
      EXPRESSIONS.neutral;


    morphMeshes.current.forEach(
      (object) => {

        const dictionary =
          object.morphTargetDictionary;

        const influences =
          object.morphTargetInfluences;


        EXPRESSION_TARGETS.forEach(
          (name) => {

            const index =
              dictionary[name];


            if (
              index === undefined
            ) {
              return;
            }


            const target =
              currentExpression[
                name
              ] || 0;


            /*
             * TRANSIÇÃO SUAVE
             */

            influences[index] =
              THREE.MathUtils.lerp(
                influences[index],
                target,
                0.12
              );

          }
        );

      }
    );


    /*
     * =====================================
     * PISCAR NATURAL
     * =====================================
     */

    if (
      blinkStart.current === null &&
      time >=
        nextBlink.current
    ) {

      blinkStart.current =
        time;

    }


    let blink = 0;


    if (
      blinkStart.current !== null
    ) {

      const elapsed =
        time -
        blinkStart.current;


      const duration =
        0.22;


      /*
       * FECHAR
       */

      if (
        elapsed <
        duration / 2
      ) {

        blink =
          elapsed /
          (duration / 2);

      }


      /*
       * ABRIR
       */

      else if (
        elapsed <
        duration
      ) {

        blink =
          1 -
          (
            elapsed -
            duration / 2
          ) /
          (duration / 2);

      }


      /*
       * TERMINAR
       */

      else {

        blink = 0;

        blinkStart.current =
          null;


        /*
         * PRÓXIMO PISCAR
         * ENTRE 2.5 E 6 SEGUNDOS
         */

        nextBlink.current =
          time +
          2.5 +
          Math.random() *
            3.5;

      }

    }


    /*
     * APLICAR BLINK
     */

    blinkTargets.current.forEach(
      ({
        object,
        leftIndex,
        rightIndex,
      }) => {

        if (
          leftIndex !== undefined
        ) {

          object
            .morphTargetInfluences[
              leftIndex
            ] = blink;

        }


        if (
          rightIndex !== undefined
        ) {

          object
            .morphTargetInfluences[
              rightIndex
            ] = blink;

        }

      }
    );

  });


  /*
   * =====================================
   * RENDERIZAR AVATAR
   * =====================================
   */

  return (
    <primitive
      object={scene}
      position={[0, 0, 0]}
      rotation={[0, 0, 0]}
      scale={1}
    />
  );

}


/*
 * PRELOAD
 */

useGLTF.preload(
  "/models/baghdad_idle_v2.glb"
);