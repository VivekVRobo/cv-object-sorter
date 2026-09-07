import argparse
from pathlib import Path

from .actuator import SortActuator
from .colors import load_color_ranges
from .detector import detect_colored_objects
from .trigger import PassageTrigger


def build_parser():
    p = argparse.ArgumentParser(description="OpenCV color object sorter")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--port", help="Serial port for sorter actuator")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--config", default=str(Path(__file__).resolve().parents[2] / "config" / "colors.yaml"))
    p.add_argument("--min-area", type=float, default=900.0)
    p.add_argument("--gate-width", type=int, default=50, help="Trigger band width around frame center")
    p.add_argument("--stable-frames", type=int, default=3, help="Consecutive in-gate frames required before firing")
    p.add_argument("--reset-frames", type=int, default=3, help="Consecutive clear/outside frames required to re-arm")
    p.add_argument("--cooldown-s", type=float, default=1.0, help="Actuator minimum time between accepted commands")
    return p


def run():
    args = build_parser().parse_args()
    import cv2

    if args.gate_width < 1:
        raise SystemExit("--gate-width must be >= 1")
    if args.cooldown_s < 0:
        raise SystemExit("--cooldown-s must be >= 0")

    serial_handle = None
    if not args.dry_run:
        if not args.port:
            raise SystemExit("--port is required unless --dry-run is used")
        import serial
        serial_handle = serial.Serial(args.port, args.baud, timeout=0.1)

    colors = load_color_ranges(args.config)
    actuator = SortActuator(serial_handle, cooldown_s=args.cooldown_s)
    trigger = PassageTrigger(
        stable_frames_required=args.stable_frames,
        reset_frames_required=args.reset_frames,
    )
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {args.camera}")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            height, width = frame.shape[:2]
            gate_left = width // 2 - args.gate_width // 2
            gate_right = width // 2 + args.gate_width // 2
            cv2.rectangle(frame, (gate_left, 0), (gate_right, height), (255, 255, 255), 1)

            detections = detect_colored_objects(frame, colors, args.min_area)
            primary = detections[0] if detections else None

            if primary:
                x, y, w, h = primary.bbox
                cx, cy = primary.centroid
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
                cv2.putText(
                    frame,
                    primary.label,
                    (x, max(20, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )
                decision = trigger.update(primary.label, cx, gate_left, gate_right)
            else:
                decision = trigger.update(None, None, gate_left, gate_right)

            if decision.fire and decision.label is not None:
                accepted = actuator.sort(decision.label)
                if not accepted:
                    print(
                        "WARN trigger fired but actuator cooldown rejected command; "
                        "increase object spacing or reduce --cooldown-s only after validating the mechanism"
                    )

            status = f"trigger={decision.reason} stable={decision.stable_frames} latched={decision.latched}"
            cv2.putText(
                frame,
                status,
                (10, height - 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
            )

            cv2.imshow("CV Object Sorter", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if serial_handle is not None:
            serial_handle.close()


if __name__ == "__main__":
    run()
