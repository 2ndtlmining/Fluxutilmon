import aiohttp
import asyncio
import json
import os
import datetime

benchurl = "https://stats.runonflux.io/fluxinfo?projection=benchmark"
utilurl = "https://stats.runonflux.io/fluxinfo?projection=apps.resources"
totalnodeurl = "https://api.runonflux.io/daemon/getzelnodecount"
walleturl = "https://api.runonflux.io/daemon/viewdeterministiczelnodelist"

async def fetch_bench_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Request failed with status code: {response.status}")
    except aiohttp.ClientError as e:
        # Handle any other request-related errors
        print(f"An error occurred: {str(e)}")
        return None
        

async def fetch_wallet_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Request failed with status code: {response.status}")
    except aiohttp.ClientError as e:
        # Handle any other request-related errors
        print(f"An error occurred: {str(e)}")
        return None
        
async def fetch_util_data(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'error' and data.get('data', {}).get('message') == 'Internal error. Try again later':
                        raise Exception('Internal error. Try again later')
                    return data
                else:
                    raise Exception(f"Request failed with status code: {response.status}")
                
    except aiohttp.ClientError as e:
        # Handle any other request-related errors
        print(f"An error occurred: {str(e)}")
        return None
        
async def fetch_totalnodes(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data


async def main():
    bench_data = await fetch_bench_data(benchurl)
    util_data = await fetch_util_data(utilurl)
    total_nodes_data = await fetch_totalnodes(totalnodeurl)
    wallet_data = await fetch_wallet_data(walleturl)

    try:
        totalbenchmarkcores = sum(record['benchmark']['bench']['cores'] for record in bench_data['data'])
        totalbenchmarkram = sum(record['benchmark']['bench']['ram'] for record in bench_data['data'])
        totalbenchmarkssd = sum(record['benchmark']['bench']['ssd'] for record in bench_data['data'])
        
        totalutilcores = sum(record['apps']['resources']['appsCpusLocked'] for record in util_data['data'])
        totalutilram = ((sum(record['apps']['resources']['appsRamLocked'] for record in util_data['data']))) / 1000
        totalutilssd = sum(record['apps']['resources']['appsHddLocked'] for record in util_data['data'])
    
        notutilizednodes = sum(1 for record in util_data['data'] if record['apps']['resources']['appsRamLocked'] == 0)
    
        totalnodes = total_nodes_data['data']['total']
        total_cumulus = total_nodes_data['data']['cumulus-enabled']
        total_nimbus = total_nodes_data['data']['nimbus-enabled']
        total_stratus = total_nodes_data['data']['stratus-enabled']
    
        utilization_percentage_cores = (totalutilcores / totalbenchmarkcores) * 100
        utilization_percentage_ram = (totalutilram / totalbenchmarkram) * 100
        utilization_percentage_ssd = (totalutilssd / totalbenchmarkssd) * 100
        utilization_nodes = (totalnodes - notutilizednodes) / totalnodes * 100
        snapshot_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


     # Unique wallet ids
        unique_wallet_ids = set(record['payment_address'] for record in wallet_data['data'])
        unique_wallet_count = len(unique_wallet_ids)  # Calculate the count of unique wallet ids
        print(f'Unique Wallet IDs: {unique_wallet_count}')
    except (KeyError, TypeError) as e:
        print(f"Error processing bench_data: {str(e)}")
        # Handle the error gracefully, e.g., retry later or continue without creating the JSON file

    

    jsondata = {
        'Snapshot': snapshot_date,
        'totalbenchmarkcores': totalbenchmarkcores,
        'totalbenchmarkram': totalbenchmarkram,
        'totalbenchmarkssd': totalbenchmarkssd,
        'totalutilcores': totalutilcores,
        'totalutilram': totalutilram,
        'totalutilssd': totalutilssd,
        'notutilizednodes': notutilizednodes,
        'totalnodes': totalnodes,
        'utilization_percentage_cores': utilization_percentage_cores,
        'utilization_percentage_ram': utilization_percentage_ram,
        'utilization_percentage_ssd': utilization_percentage_ssd,
        'utilization_nodes': utilization_nodes,
        'total_cumulus': total_cumulus,
        'total_nimbus': total_nimbus,
        'total_stratus': total_stratus,
        'unique_wallet_count': unique_wallet_count

    }
    filename = f'utilization_{snapshot_date}.json'
    filepath = os.path.join('data', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(jsondata, f, indent=4)

    print(f'Data written to {filepath}')
    
    print(f'Total benchmark Threads: {totalbenchmarkcores}')
    print(f'Total benchmark Ram: {totalbenchmarkram}')
    print(f'Total benchmark SSD: {totalbenchmarkssd}')
    
    print(f'Total Util Threads: {totalutilcores}')
    print(f'Total Util Ram: {totalutilram}')
    print(f'Total Util SSD: {totalutilssd}')
    
    print(f'Number unutilized Nodes: {notutilizednodes}')
    print(f'Total amount of Nodes = {totalnodes}')
    print(f'Total amount of Cumulus = {total_cumulus}')
    print(f'Total amount of Nimbus = {total_nimbus}')
    print(f'Total amount of Stratus = {total_stratus}')
    
    print(f'Utilization Percentage (Cores): {utilization_percentage_cores:.2f}%')
    print(f'Utilization Percentage (Ram): {utilization_percentage_ram:.2f}%')
    print(f'Utilization Percentage (SSD): {utilization_percentage_ssd:.2f}%')
    print(f'Utilization Nodes: {utilization_nodes:.2f}%')
    print(f'Unique Wallet IDs: {unique_wallet_count}')

# Create and run the event loop
# Create and run the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.close()