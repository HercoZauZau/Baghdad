import {
  useEffect,
  useRef,
} from "react";

import {
  useFrame,
} from "@react-three/fiber";

import {
  useAnimations,
  useGLTF,
} from "@react-three/drei";

import * as THREE from "three";


// ============================================================
// VISEMES
// ============================================================

const VISEMES = [
  "PP",
  "FF",
  "TH",
  "DD",
  "kk",
  "CH",
  "SS",
  "nn",
  "RR",
  "aa",
  "E",
  "ih",
  "oh",
  "ou",
];


// ============================================================
// RHUBARB → METAPERSON
// ============================================================

const RHUBARB_TO_VISEME = {

  A: "PP",

  B: "SS",

  C: "E",

  D: "aa",

  E: "oh",

  F: "ou",

  G: "FF",

  H: "nn",

  X: null,

};


// ============================================================
// EXPRESSÕES
// ============================================================

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

  "mouthPressLeft",
  "mouthPressRight",

];


// ============================================================
// AVATAR
// ============================================================

export default function Avatar({

  expression = "neutral",

  speech = null,

  state = "idle",

  onSpeechEnd,

}) {


  const {
    scene,
    animations,
  } = useGLTF(
    "/models/baghdad_idle_v2.glb"
  );


  const {
    actions,
  } = useAnimations(
    animations,
    scene
  );


  const morphMeshes =
    useRef([]);


  const blinkTargets =
    useRef([]);


  const visemeMeshes =
    useRef([]);


  const audioRef =
    useRef(null);


  const mouthCuesRef =
    useRef([]);


  const nextBlink =
    useRef(2);


  const blinkStart =
    useRef(null);


  // ==========================================================
  // ANALISAR MODELO
  // ==========================================================

  useEffect(() => {

    morphMeshes.current = [];

    blinkTargets.current = [];

    visemeMeshes.current = [];


    scene.traverse(
      (object) => {


        if (
          !object.morphTargetDictionary ||
          !object.morphTargetInfluences
        ) {
          return;
        }


        morphMeshes.current.push(
          object
        );


        const dictionary =
          object.morphTargetDictionary;


        const encontrados =
          VISEMES.filter(
            (name) =>
              dictionary[name]
              !== undefined
          );


        if (
          encontrados.length > 0
        ) {

          visemeMeshes.current.push(
            object
          );

        }


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

      }
    );

  }, [scene]);


  // ==========================================================
  // IDLE
  // ==========================================================

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


  // ==========================================================
  // NOVA FALA
  // ==========================================================

  useEffect(() => {

    if (
      !speech?.audioUrl
    ) {
      return;
    }


    /*
     * Parar áudio anterior.
     */

    if (
      audioRef.current
    ) {

      audioRef.current.pause();

      audioRef.current.onended =
        null;

    }


    mouthCuesRef.current =
      speech.mouthCues || [];


    const audio =
      new Audio(
        speech.audioUrl
      );


    audio.preload =
      "auto";


    /*
     * MUITO IMPORTANTE:
     *
     * É este evento que informa
     * o App.jsx de que Baghdad
     * terminou realmente de falar.
     */

    audio.onended = () => {

      console.log(
        "Áudio terminado."
      );


      mouthCuesRef.current =
        [];


      audioRef.current =
        null;


      if (
        onSpeechEnd
      ) {

        onSpeechEnd();

      }

    };


    audio.onerror = (
      audioError
    ) => {

      console.error(
        "Erro no áudio:",
        audioError
      );


      mouthCuesRef.current =
        [];


      if (
        onSpeechEnd
      ) {

        onSpeechEnd();

      }

    };


    audioRef.current =
      audio;


    audio.play().catch(
      (playError) => {

        console.error(
          "Erro ao reproduzir áudio:",
          playError
        );


        if (
          onSpeechEnd
        ) {

          onSpeechEnd();

        }

      }
    );


    return () => {

      audio.pause();

      audio.onended = null;

      audio.onerror = null;

    };

  }, [
    speech,
    onSpeechEnd,
  ]);


  // ==========================================================
  // LOOP
  // ==========================================================

  useFrame(
    ({ clock }) => {


      const time =
        clock.getElapsedTime();


      const currentExpression =
        EXPRESSIONS[
          expression
        ]
        ||
        EXPRESSIONS.neutral;


      // ======================================================
      // EXPRESSÕES
      // ======================================================

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
                ]
                || 0;


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


      // ======================================================
      // LIP-SYNC + COARTICULAÇÃO
      // ======================================================

      const audio =
        audioRef.current;


      let currentViseme =
        null;


      let nextViseme =
        null;


      let currentWeight =
        0;


      let nextWeight =
        0;


      if (
        audio &&
        !audio.paused &&
        !audio.ended
      ) {


        const currentTime =
          audio.currentTime;


        const cues =
          mouthCuesRef.current;


        const cueIndex =
          cues.findIndex(
            (cue) =>
              currentTime >= cue.start &&
              currentTime < cue.end
          );


        if (
          cueIndex !== -1
        ) {


          const cue =
            cues[
              cueIndex
            ];


          const nextCue =
            cues[
              cueIndex + 1
            ];


          currentViseme =
            RHUBARB_TO_VISEME[
              cue.value
            ]
            || null;


          const timeToEnd =
            cue.end -
            currentTime;


          const transitionWindow =
            0.08;


          if (
            nextCue &&
            timeToEnd <
              transitionWindow
          ) {


            nextViseme =
              RHUBARB_TO_VISEME[
                nextCue.value
              ]
              || null;


            const blend =
              THREE.MathUtils.clamp(

                1 -
                  timeToEnd /
                  transitionWindow,

                0,

                1

              );


            currentWeight =
              1 - blend;


            nextWeight =
              blend;

          }

          else {

            currentWeight =
              1;

          }

        }

      }


      // ======================================================
      // APLICAR VISEMES
      // ======================================================

      visemeMeshes.current.forEach(
        (object) => {


          const dictionary =
            object.morphTargetDictionary;


          const influences =
            object.morphTargetInfluences;


          VISEMES.forEach(
            (name) => {


              const index =
                dictionary[name];


              if (
                index === undefined
              ) {
                return;
              }


              let target =
                0;


              if (
                name ===
                currentViseme
              ) {

                target +=
                  currentWeight *
                  0.9;

              }


              if (
                name ===
                nextViseme
              ) {

                target +=
                  nextWeight *
                  0.9;

              }


              influences[index] =
                THREE.MathUtils.lerp(

                  influences[index],

                  target,

                  0.45

                );

            }
          );


          // --------------------------------------------------
          // MAXILAR
          // --------------------------------------------------

          const jawIndex =
            dictionary.jawOpen;


          if (
            jawIndex !== undefined
          ) {


            let jawTarget =
              0;


            if (
              currentViseme === "aa"
            ) {

              jawTarget =
                0.35 *
                currentWeight;

            }


            else if (
              currentViseme === "E"
            ) {

              jawTarget =
                0.18 *
                currentWeight;

            }


            else if (
              currentViseme === "oh"
            ) {

              jawTarget =
                0.22 *
                currentWeight;

            }


            else if (
              currentViseme === "ou"
            ) {

              jawTarget =
                0.12 *
                currentWeight;

            }


            if (
              nextViseme === "aa"
            ) {

              jawTarget +=
                0.35 *
                nextWeight;

            }


            influences[jawIndex] =
              THREE.MathUtils.lerp(

                influences[
                  jawIndex
                ],

                jawTarget,

                0.35

              );

          }

        }
      );


      // ======================================================
      // PISCAR
      // ======================================================

      if (
        blinkStart.current === null &&
        time >= nextBlink.current
      ) {

        blinkStart.current =
          time;

      }


      let blink =
        0;


      if (
        blinkStart.current !== null
      ) {


        const elapsed =
          time -
          blinkStart.current;


        const duration =
          0.22;


        if (
          elapsed <
          duration / 2
        ) {

          blink =
            elapsed /
            (
              duration / 2
            );

        }


        else if (
          elapsed < duration
        ) {

          blink =
            1 -
            (
              elapsed -
              duration / 2
            )
            /
            (
              duration / 2
            );

        }


        else {

          blink =
            0;


          blinkStart.current =
            null;


          nextBlink.current =
            time
            +
            2.5
            +
            Math.random()
            * 3.5;

        }

      }


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

    }
  );


  return (

    <primitive

      object={scene}

      position={[
        0,
        0,
        0
      ]}

      rotation={[
        0,
        0,
        0
      ]}

      scale={1}

    />

  );

}


useGLTF.preload(
  "/models/baghdad_idle_v2.glb"
);