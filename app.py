from pathlib import Path
import argparse
import json
from src.auth import authenticate_vehicle
from src.data import CITIES, get_city_attractions_fallback
from src.history import save_history_entry
from src.llm_local import fetch_city_attractions
from src.reporting import build_pdf_report
from src.search import run_algorithm, run_all_algorithms
from src.utils import pretty_trace, now_iso


def parse_args():
    parser = argparse.ArgumentParser(description='Trabalho Prático Final — Métodos de Procura, OCR e LLM')
    parser.add_argument('--plate', help='Matrícula do veículo')
    parser.add_argument('--plate-image', help='Imagem da matrícula para OCR')
    parser.add_argument('--origin', required=True, help='Cidade de origem')
    parser.add_argument('--goal', required=True, help='Cidade de destino')
    parser.add_argument('--algorithm', choices=['ucs', 'dls', 'greedy', 'astar', 'all'], default='all')
    parser.add_argument('--depth-limit', type=int, default=10)
    parser.add_argument('--llm-model', default='llama3.1:8b')
    parser.add_argument('--output-dir', default='outputs')
    parser.add_argument('--generate-report', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.origin not in CITIES or args.goal not in CITIES:
        raise SystemExit(f'Origem e destino devem pertencer ao conjunto de cidades suportadas: {", ".join(CITIES)}')

    auth_result = authenticate_vehicle(plate=args.plate, image_path=args.plate_image)
    if not auth_result['authenticated']:
        raise SystemExit(f"Falha de autenticação: {auth_result['message']}")

    if args.algorithm == 'all':
        results = run_all_algorithms(args.origin, args.goal, depth_limit=args.depth_limit)
    else:
        results = {args.algorithm: run_algorithm(args.algorithm, args.origin, args.goal, depth_limit=args.depth_limit)}

    print('\n=== AUTENTICAÇÃO ===')
    print(json.dumps(auth_result, ensure_ascii=False, indent=2))

    print('\n=== RESULTADOS DE PROCURA ===')
    for name, result in results.items():
        print(f'\n--- {name.upper()} ---')
        print(pretty_trace(result))

    attractions = {}
    for city in sorted({args.origin, args.goal}):
        attractions[city] = fetch_city_attractions(city, model=args.llm_model)
        if not attractions[city]:
            attractions[city] = get_city_attractions_fallback(city)

    print('\n=== ATRAÇÕES ===')
    print(json.dumps(attractions, ensure_ascii=False, indent=2))

    history_entry = {
        'timestamp': now_iso(),
        'vehicle': auth_result,
        'origin': args.origin,
        'goal': args.goal,
        'algorithm': args.algorithm,
        'depth_limit': args.depth_limit,
        'results': results,
        'attractions': attractions,
    }
    save_history_entry(history_entry)

    if args.generate_report:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / f"relatorio_{args.origin}_{args.goal}_{args.algorithm}.pdf"
        build_pdf_report(report_path, history_entry)
        print(f'\nRelatório PDF gerado em: {report_path}')


if __name__ == '__main__':
    main()
